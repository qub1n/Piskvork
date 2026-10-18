#include <windows.h>
#include <iostream>
#include <string>
#include <stdlib.h>

// Tiny protocol fixture: two near-deadline decisions, then Black completes five.
int main(int argc,char**argv) {
    const bool slow=std::string(argv[0]).find("slow")!=std::string::npos;
    const char* delay=getenv("PISKVORK_TEST_DELAY_MS");
    unsigned ms=delay ? strtoul(delay,0,10) : 4920;
    int turns=0;bool board=false;std::string line;
    while(std::getline(std::cin,line)) {
        if(!line.empty() && line.back()=='\r') line.pop_back();
        if(line.compare(0,6,"START ")==0 || line=="RESTART") {std::cout<<"OK"<<std::endl;continue;}
        if(line=="END") break;
        if(line=="BOARD") {board=true;continue;}
        if(board && line!="DONE") continue;
        if(line=="DONE" || line=="BEGIN" || line.compare(0,5,"TURN ")==0) {
            board=false;
            if(slow) Sleep(ms);
            std::cout<<"DEBUG fixture decision "<<turns<<std::endl;
            std::cout<<"MESSAGE fixture decision "<<turns<<std::endl;
            if(slow) std::cout<<(turns ? "4,0" : "5,5")<<std::endl;
            else std::cout<<"8,"<<(8+turns)<<std::endl;
            ++turns;
        }
    }
}
