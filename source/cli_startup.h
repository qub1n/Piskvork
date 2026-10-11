#pragma once
#include <stdlib.h>
#include <string.h>

struct CliStartup {
    bool noRegistry, benchmark;
    int size;
    const char *settingsFile;
    CliStartup(): noRegistry(false), benchmark(false), size(0), settingsFile(0) {}
};

// Read before any registry or window access. Existing match switches are parsed later.
inline bool parseCliStartup(int argc, char **argv, CliStartup &options)
{
    bool players = false;
    for(int i=1; i<argc; ++i){
        if(!strcmp(argv[i], "-p")){
            if(i+2 >= argc) return false;
            players = true;
            i += 2;
        }
        else if(!strcmp(argv[i], "-no-registry")) options.noRegistry = true;
        else if(!strcmp(argv[i], "-benchmark")) options.benchmark = options.noRegistry = true;
        else if(!strcmp(argv[i], "-size")){
            if(++i >= argc || !*argv[i]) return false;
            for(const char *p=argv[i]; *p; ++p) if(*p<'0' || *p>'9') return false;
            char *end;
            long size = strtol(argv[i], &end, 10);
            if(*end || size<5 || size>80) return false;
            options.size = (int)size;
        }
        else if(!strcmp(argv[i], "-print-settings")){
            if(++i >= argc || !*argv[i]) return false;
            options.settingsFile = argv[i];
        }
    }
    return !options.benchmark || players || options.settingsFile;
}
