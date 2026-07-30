#include "mos/core/assembly_log.hpp"

#include <algorithm>
#include <sstream>

namespace mos {
namespace core {

const char *operator_type_name(OperatorType t) noexcept {
  switch (t) {
  case OperatorType::READ_ONLY:
    return "READ_ONLY";
  case OperatorType::MUTATION:
    return "MUTATION";
  }
  return "?";
}

const char *deferral_name(AssemblyLog::Deferral d) noexcept {
  switch (d) {
  case AssemblyLog::Deferral::SupportOverlap:
    return "support-overlap";
  case AssemblyLog::Deferral::SliceLocked:
    return "slice-locked";
  case AssemblyLog::Deferral::GlobalNeedsEmpty:
    return "global-needs-empty-slice";
  }
  return "?";
}

void AssemblyLog::begin_run() {
  std::lock_guard<std::mutex> lock(mu_);
  ++runs_;
  round_ = 0;
}

void AssemblyLog::record_slice(SliceRecord rec) {
  std::lock_guard<std::mutex> lock(mu_);
  rec.round = round_++;
  slices_.push_back(std::move(rec));
}

std::vector<AssemblyLog::SliceRecord> AssemblyLog::slices() const {
  std::lock_guard<std::mutex> lock(mu_);
  return slices_;
}

std::size_t AssemblyLog::run_count() const {
  std::lock_guard<std::mutex> lock(mu_);
  return runs_;
}

namespace {
AssemblyLog::Pair canonical(const std::string &a, const std::string &b) {
  return (a <= b) ? AssemblyLog::Pair{a, b} : AssemblyLog::Pair{b, a};
}
} // namespace

std::map<AssemblyLog::Pair, std::size_t>
AssemblyLog::co_scheduling_counts() const {
  std::lock_guard<std::mutex> lock(mu_);
  std::map<Pair, std::size_t> out;
  for (const auto &s : slices_) {
    for (std::size_t i = 0; i < s.co_scheduled.size(); ++i) {
      for (std::size_t j = i + 1; j < s.co_scheduled.size(); ++j) {
        ++out[canonical(s.co_scheduled[i].name, s.co_scheduled[j].name)];
      }
    }
  }
  return out;
}

std::map<AssemblyLog::Pair, std::size_t> AssemblyLog::refused_counts() const {
  std::lock_guard<std::mutex> lock(mu_);
  std::map<Pair, std::size_t> out;
  for (const auto &s : slices_) {
    // A refusal is only evidence when both operators were present in the SAME
    // round and did not end up in the same slice. Deferred-vs-deferred also
    // counts: two nodes pushed to a later slice were both offered here.
    for (const auto &d : s.deferred) {
      for (const auto &c : s.co_scheduled) {
        ++out[canonical(d.first.name, c.name)];
      }
    }
    for (std::size_t i = 0; i < s.deferred.size(); ++i) {
      for (std::size_t j = i + 1; j < s.deferred.size(); ++j) {
        ++out[canonical(s.deferred[i].first.name, s.deferred[j].first.name)];
      }
    }
  }
  return out;
}

std::vector<std::string> AssemblyLog::format() const {
  std::lock_guard<std::mutex> lock(mu_);
  std::vector<std::string> out;
  out.reserve(slices_.size());
  for (const auto &s : slices_) {
    std::ostringstream os;
    os << "round " << s.round << ": offered=" << s.offered << " slice=[";
    for (std::size_t i = 0; i < s.co_scheduled.size(); ++i) {
      if (i) os << ", ";
      os << s.co_scheduled[i].name << "/"
         << operator_type_name(s.co_scheduled[i].type) << "{";
      bool first = true;
      for (int v : s.co_scheduled[i].support) {
        if (!first) os << ",";
        os << v;
        first = false;
      }
      os << "}";
    }
    os << "]";
    if (!s.deferred.empty()) {
      os << " deferred=[";
      for (std::size_t i = 0; i < s.deferred.size(); ++i) {
        if (i) os << ", ";
        os << s.deferred[i].first.name << ":" << deferral_name(s.deferred[i].second);
      }
      os << "]";
    }
    if (s.slice_locked_by_global_mutation) os << " LOCKED";
    out.push_back(os.str());
  }
  return out;
}

void AssemblyLog::clear() {
  std::lock_guard<std::mutex> lock(mu_);
  slices_.clear();
  runs_ = 0;
  round_ = 0;
}

AssemblyLog &assembly_log() noexcept {
  static AssemblyLog instance;
  return instance;
}

} // namespace core
} // namespace mos
