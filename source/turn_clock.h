#pragma once
#include <stdint.h>

// Protocol time excludes manager bookkeeping before a request and after a reply.
// Unsigned subtraction also works across the 32-bit monotonic tick wrap.
class TurnClock {
    bool started_, stopped_;
    uint32_t start_, stop_;
public:
    TurnClock() { prepare(); }
    void prepare() { started_ = stopped_ = false; start_ = stop_ = 0; }
    void start(uint32_t now) { start_ = now; started_ = true; stopped_ = false; }
    void stop(uint32_t now) { if (started_ && !stopped_) { stop_ = now; stopped_ = true; } }
    bool started() const { return started_; }
    bool stopped() const { return stopped_; }
    uint32_t elapsed(uint32_t now) const {
        return started_ ? (stopped_ ? stop_ : now) - start_ : 0;
    }
};
