#include "../source/cli_startup.h"
#include <assert.h>

bool parse(const char *command[], int count, CliStartup &options){
    return parseCliStartup(count, (char**)command, options);
}
int main(){
    { const char *args[]={"piskvork", "-benchmark", "-size", "15", "-p", "one.exe", "two.exe"};
      CliStartup o; assert(parse(args,7,o)); assert(o.noRegistry && o.benchmark && o.size==15); }
    { const char *args[]={"piskvork", "-size", "20"};
      CliStartup o; assert(parse(args,3,o)); assert(!o.noRegistry && o.size==20); }
    { const char *args[]={"piskvork", "-benchmark"}; CliStartup o; assert(!parse(args,2,o)); }
    { const char *args[]={"piskvork", "-size"}; CliStartup o; assert(!parse(args,2,o)); }
    const char *bad[]={"0", "81", "15junk", "-15", "999999999999999999999999", ""};
    for(int i=0;i<6;++i){const char *args[]={"piskvork","-size",bad[i]}; CliStartup o; assert(!parse(args,3,o));}
    { const char *args[]={"piskvork", "-benchmark", "-print-settings", "settings.json"};
      CliStartup o; assert(parse(args,4,o)); assert(o.settingsFile && o.noRegistry); }
    return 0;
}
