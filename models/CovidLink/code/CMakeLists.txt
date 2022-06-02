project (CovidUppaal)
set(CMAKE_CXX_STANDARD 20)
include (FetchContent)
FetchContent_Declare(covidsim
        GIT_REPOSITORY git@github.com:dannybpoulsen/covidsim.git
	GIT_TAG 44e93bb063c62f207623c5cf5df7f9c1eebcb660
)

FetchContent_MakeAvailable(covidsim)


add_library (covidlink SHARED CovidLink.cpp)
target_link_libraries (covidlink PUBLIC  asan covid  )






