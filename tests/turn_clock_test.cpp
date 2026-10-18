#include "../source/turn_clock.h"
#include <assert.h>
#include <iostream>

int main() {
    TurnClock clock;
    assert(!clock.started() && clock.elapsed(100000)==0);
    clock.start(100000); // manager preparation took arbitrarily long
    assert(clock.elapsed(104920)==4920);
    clock.stop(104920);
    assert(clock.elapsed(110000)==4920); // logging/UI cannot create a timeout
    clock.stop(111000);
    assert(clock.elapsed(112000)==4920); // first complete reply wins
    clock.prepare();
    assert(!clock.started() && clock.elapsed(120000)==0);
    clock.start(120000);
    clock.stop(125001);
    assert(clock.elapsed(130000)>5000); // a late reply still exceeds the same limit
    clock.prepare();
    clock.start(0xfffffff0u);
    assert(clock.elapsed(0x10u)==32);
    clock.stop(0x20u);
    assert(clock.elapsed(0x100u)==48);
    std::cout<<"Protocol clock boundary regression passed\n";
}
