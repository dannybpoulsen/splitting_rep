project (CovidUppaal)
set(CMAKE_CXX_STANDARD 20)
include (FetchContent)
FetchContent_Declare(covidsim
        GIT_REPOSITORY git@github.com:dannybpoulsen/covidsim.git
	GIT_TAG a830fb836814628fc33a23c63d559b78bb55c054
)

FetchContent_MakeAvailable(covidsim)


add_library (covidlink SHARED CovidLink.cpp)
target_link_libraries (covidlink PUBLIC  asan covid  )






