import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
class TlsClockTests(unittest.TestCase):
 def test_clock_bounds_and_utc_conversion(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/"clock.cc"
   f.write_text(r"""
#include "network_time.h"
#include <cassert>
#include <limits>
int main(){
 using namespace NetworkTime;
 assert(!ClockPlausible(0)); assert(ClockPlausible(1790000000));
 int polls=0, sleeps=0;
 assert(!WaitUntilReady(1000,[]{return time_t(0);},[&](unsigned n){assert(n<=100);++sleeps;}));
 assert(sleeps==10);
 assert(WaitUntilReady(1000,[&]{return ++polls>=3?time_t(1790000000):time_t(0);},[](unsigned){}));
 assert(NeedsClock("https://example.test",true)); assert(NeedsClock("wss://example.test",true));
 assert(!NeedsClock("http://example.test",true)); assert(!NeedsClock("https://example.test",false));
 timeval tv{}; assert(ServerTimeval(1790000000123.,tv));assert(tv.tv_sec==1790000000);assert(tv.tv_usec==123000);
 for(double offset:{480.,-330.,0.}){assert(!PosixTimezone(offset).empty());assert(ServerTimeval(1790000000123.,tv));assert(tv.tv_sec==1790000000);}
 assert(PosixTimezone(480)=="UTC-08:00");assert(PosixTimezone(-330)=="UTC+05:30");
 assert(PosixTimezone(999999).empty());
 assert(!ServerTimeval(-1,tv));assert(!ServerTimeval(0,tv));
 assert(!ServerTimeval(std::numeric_limits<double>::infinity(),tv));
 assert(!ServerTimeval(std::numeric_limits<double>::quiet_NaN(),tv));
 assert(!ServerTimeval(1e30,tv));
}""")
   exe=Path(tmp)/"clock"
   subprocess.run([shutil.which("c++"),"-std=c++17","-Wall","-Wextra","-Werror","-I",str(ROOT/"main"),str(f),"-o",str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
 def test_guards_cover_assets_and_ota(self):
  ota=(ROOT/"main/ota.cc").read_text()
  self.assertLess(ota.index("NetworkTime::WaitForTls"),ota.index('http->Open(method, url)'))
  self.assertNotIn('ts += (timezone_offset',ota)
  app=(ROOT/"main/application.cc").read_text()
  part=app[app.index("void Application::CheckAssetsVersion"):app.index("void Application::CheckNewVersion")]
  self.assertLess(part.index("NetworkTime::WaitForTls"),part.index('settings.EraseKey("download_url")'))
  wifi=(ROOT/"main/boards/common/wifi_board.cc").read_text()
  self.assertIn("NetworkTime::StartSync()",wifi)
  cfg=json.loads((ROOT/"main/boards/lckfb/szpi-esp32s3/config.json").read_text())
  self.assertIn("CONFIG_MBEDTLS_HAVE_TIME_DATE=y",cfg["builds"][0]["sdkconfig_append"])

 def test_runtime_sntp_is_async_idempotent_and_wait_is_bounded(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);(folder/"freertos").mkdir()
   (folder/"sdkconfig.h").write_text("#define CONFIG_MBEDTLS_HAVE_TIME_DATE 1\n#define CONFIG_LWIP_SNTP_MAX_SERVERS 2\n")
   (folder/"esp_netif_sntp.h").write_text(r"""
#pragma once
#define ESP_OK 0
struct esp_sntp_config_t { const char* servers[2]; unsigned num_of_servers; };
#define ESP_NETIF_SNTP_DEFAULT_CONFIG(s) {{s,nullptr},1}
extern int init_calls, start_calls;
inline int esp_netif_sntp_init(const esp_sntp_config_t* c){++init_calls;return init_calls==1?-1:(c->num_of_servers==2?0:-2);}
inline int esp_netif_sntp_start(){++start_calls;return 0;}
""")
   (folder/"esp_log.h").write_text("#define ESP_LOGE(...) ((void)0)\n#define ESP_LOGW(...) ((void)0)\n")
   (folder/"freertos/FreeRTOS.h").write_text("#define pdMS_TO_TICKS(ms) (ms)\n")
   (folder/"freertos/task.h").write_text("extern unsigned slept, sync_after;\nextern long fake_now;\ninline void vTaskDelay(unsigned ms){slept+=ms;if(sync_after && slept>=sync_after)fake_now=1790000000;}\n")
   source=folder/"runtime.cc";source.write_text(r"""
#include "network_time.h"
#include <cassert>
int init_calls=0,start_calls=0;unsigned slept=0,sync_after=0;long fake_now=0;
extern "C" time_t time(time_t* out) noexcept(noexcept(std::time(nullptr))){if(out)*out=fake_now;return fake_now;}
int main(){
 NetworkTime::StartSync();assert(init_calls==1);
 NetworkTime::StartSync();assert(init_calls==2);
 NetworkTime::StartSync();assert(init_calls==2 && start_calls==1);
 assert(NetworkTime::WaitForTls("http://example.test",1000));assert(slept==0);
 assert(!NetworkTime::WaitForTls("https://example.test",1000));assert(slept==1000);
 slept=0;sync_after=300;assert(NetworkTime::WaitForTls("https://example.test",1000));assert(slept==300);
 slept=0;assert(NetworkTime::WaitForTls("https://example.test",1000));assert(slept==0);
}
""")
   exe=folder/"runtime"
   subprocess.run([shutil.which("c++"),"-std=c++17","-Wall","-Wextra","-Werror","-I",str(folder),"-I",str(ROOT/"main"),str(ROOT/"main/network_time.cc"),str(source),"-o",str(exe)],check=True)
   subprocess.run([str(exe)],check=True)

if __name__=="__main__":unittest.main()
