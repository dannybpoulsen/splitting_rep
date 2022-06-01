project (CovidUppaal)
set(CMAKE_CXX_STANDARD 20)
include (FetchContent)
FetchContent_Declare(covidsim
        GIT_REPOSITORY git@github.com:dannybpoulsen/covidsim.git
	GIT_TAG 5ec3ea88e1a7873e9074168bd0d4e8fd653b4640
)

FetchContent_MakeAvailable(covidsim)


add_library (covidlink SHARED CovidLink.cpp)
target_link_libraries (covidlink PUBLIC  asan covid  )






