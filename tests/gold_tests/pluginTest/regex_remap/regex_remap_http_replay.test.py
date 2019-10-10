'''
'''
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import time

#replay_file_dir = 'pluginregex_remap/replay/yts-2819.replay.json'
replay_file_dir = '/home/corwin/git/trafficserver/tests/gold_tests/pluginTest/regex_remap/replay/yts-2819.replay.json'
hostIP = '127.0.0.1'

data_dir = os.path.join(Test.RunDirectory, 'regex_remap_replay')

sys.stdout.write(Test.Variables["AtsTestToolsDir"])

ts,dns,replay_server, client_command = Test.ReplaySetUp(replay_file_dir)

# Configuration
regex_remap_conf_path = os.path.join(ts.Variables.CONFIGDIR, 'regex_remap.conf')

path1_rule = 'path1 {}\n'.format(int(time.time()) + 600)

ts.Disk.File(regex_remap_conf_path, typename="ats:config").AddLines([
    "# regex_remap configuration\n"
    "^/alpha/bravo/[?]((?!action=(newsfeed|calendar|contacts|notepad)).)*$ http://example.one @status=301\n"
])

ts.Disk.remap_config.AddLine(
    "map http://example.one/ http://localhost:{}/ @plugin=regex_remap.so @pparam=regex_remap.conf\n".format(replay_server.Variables.port)
)

# minimal configuration
ts.Disk.records_config.update({
    'proxy.config.diags.debug.enabled': 1,
    'proxy.config.diags.debug.tags': 'http|regex_remap',
    'proxy.config.http.cache.http': 0,
    'proxy.config.http.server_ports': '{}'.format(ts.Variables.port),
    'proxy.config.dns.nameservers': '{0}:{1}'.format(hostIP, dns.Variables.port),
})

# 0 Test - Load cache (miss) (path1)
tr = Test.AddTestRun("smoke test")
tr.Setup.MakeDir(data_dir)
tr.Setup.Copy(replay_file_dir, data_dir)
tr.Processes.Default.StartBefore(replay_server)
tr.Processes.Default.StartBefore(ts)
tr.Processes.Default.StartBefore(dns)
tr.Command = client_command
tr.Processes.Default.ReturnCode = 0
tr.Processes.Default.Streams.All = Testers.ExcludesExpression("[eE]rror","error")
ts.Disk.diags_log.Content = Testers.ContainsExpression('ERROR: .regex_remap. Bad regular expression result -21', "Resource limit exceeded")
tr.StillRunningAfter = ts
