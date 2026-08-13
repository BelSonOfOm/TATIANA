cmake_minimum_required(VERSION 3.20)
project(tatiana_v2_experiments LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Standalone on purpose: no add_subdirectory(../../MOS), no target_link_libraries against
# MOS's engine. See README.md. One add_subdirectory() per phase, added when that phase's
# first experiment exists — none yet.
