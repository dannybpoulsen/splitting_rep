project (CovidUppaal)
set(CMAKE_CXX_STANDARD 20)
include (FetchContent)
FetchContent_Declare(covidsim
        GIT_REPOSITORY git@github.com:dannybpoulsen/covidsim.git
	GIT_TAG 6f669a3b2a79df43593f5a239b20e5bed339c374
)

FetchContent_MakeAvailable(covidsim)


add_library (covidlink SHARED CovidLink.cpp)
target_link_libraries (covidlink PUBLIC  asan covid  )






