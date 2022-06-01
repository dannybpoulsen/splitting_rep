#include <chrono>
#include <cassert>
#include "core/loader.hpp"
#include "behaviour/interface.hpp"
#include "core/time.hpp"
#include "world/state.hpp"
#include "messaging/messager.hpp"
#include "core/counters.hpp"
#include "core/kommuner.hpp"
#include "core/random.hpp"
#include "world/state.hpp"
#include "behaviour/interface.hpp"
#include "behaviour/health/multistrand.hpp"
#include "behaviour/health/strandparam.hpp"
#include "behaviour/health/component.hpp"
#include "behaviour/health/venueselectors.hpp"
#include "behaviour/health/healthparams.hpp"
#include "behaviour/sporadic/sporadic_infector.hpp"
#include "behaviour/testing/test.hpp"
#include "behaviour/outputter/console.hpp"

#include "messaging/messager.hpp"

#include <array>
#include <ostream>
#include <fstream>
#include <type_traits>
#include <vector>

struct Statistics
{
  Covid::Core::counter_t currentI = 0;
  Covid::Core::counter_t currentE = 0;
  Covid::Core::counter_t currentS = 0;
  Covid::Core::counter_t currentR = 0;
  Covid::Core::counter_t currentV = 0;
  Covid::Core::counter_t currentH = 0;
	
  std::size_t currentN() const
  {
    return currentS + currentE + currentR + currentI + currentV + currentH;
  }
};    
struct SimData {
  Covid::Core::Time time;
  Covid::World::State state;
  Statistics stats;
};
class Simulator
{
public:
  Simulator(Covid::Core::Model&& model, Covid::Core::Time time) :model(std::move(model)),startTime(time) {}
  
  void addBehaviour(Covid::Behavior::Behaviour_ptr sys) {
    sys->setMessager(&messenger);
    systems.push_back(std::move(sys));
  }
  const Covid::Core::Time& simStarts() const;
  Covid::Messaging::Messenger& getMessageSystem() { return messenger;}
    
  template <class T, class... Args>
  T& makeBehaviour(Args&&... args)
  {
    std::unique_ptr<T> t = std::make_unique<T>(std::forward<Args&&>(args)...);
    if constexpr (Covid::Behavior::BehaviourTrait<T>::needs_messager()) {
      getMessageSystem().addListener(t.get());
    }
    auto* res = t.get();
      addBehaviour(std::move(t));
      return *res;
    }

  void startSim ();

  void stepSim (SimData& data) {
    Covid::Core::TimeDelta delta{4};
    for (auto& sys : systems) {
      sys->update(delta, data.time, data.state);
    }
    data.time = data.time.add(delta);
    
  }
  
   
  
  private:
    Covid::Messaging::Messenger messenger;
    std::vector<Covid::Behavior::Behaviour_ptr> systems;
    Covid::Core::Model model;
    Covid::Core::Time startTime;
  };

    class SEIRCounter : public Covid::Behavior::IBehaviour, public Covid::Messaging::MessageListener
    {
    public:

      virtual void update(const Covid::Core::TimeDelta&, const Covid::Core::Time& t, Covid::World::State& s)
      {
      }

      virtual SEIRCounter& addAgent(Covid::World::AgentState& agent) { return *this; }
      
      virtual void initialise(Covid::World::State& worldstate, const Covid::Core::Time&)
      {
      }
      
      virtual void recvMessage(const Covid::Messaging::Message& m);
  
      
    };

namespace Covid {
  namespace Behavior {
    template <>
    struct BehaviourTrait<SEIRCounter>
    {
      static constexpr bool needs_messager() { return true; }
    };
    
  }
}


struct GlobalState {
  GlobalState () : simulator( Covid::Core::loadModel<Covid::Core::ModelSource::Random,
			      const Covid::Core::RandomModelInput&> (
								     Covid::Core::RandomModelInput{
								       .agents = 10000,
								       .homes = 100,
								       .schools =100,
								       .leisure = 1000}),
			      Covid::Core::Time{}
			      
			      ){
     
    simulator.makeBehaviour<SEIRCounter> ();
     auto hparam = std::make_unique<Covid::Behavior::Health::MultiStrandParamProvider>();
     hparam->enableStrand<Covid::World::Variant::Alpha> ();

     
     Covid::Behavior::Health::CovidParam<Covid::World::Variant::Alpha>::setBeta (0.5);
     Covid::Behavior::Health::CovidParam<Covid::World::Variant::Alpha>::setAsymp (0.8);
     
     
     auto venue_selector = std::make_unique<Covid::Behavior::Health::FixedVenueSelector>();
     auto hinit = std::make_unique<Covid::Behavior::Health::UniformHealthInitialiser>(0.01, 0);
     simulator.makeBehaviour<Covid::Behavior::Health::HealthLocationImpl>(std::move(hparam),
									  std::move(venue_selector),
									  std::move(hinit));
     
     simulator.makeBehaviour<Covid::Behavior::ExponentialWaiting<Covid::World::Variant::Alpha>>(
												Covid::Core::Time{}, Covid::Core::Time{}.add({0,1,0,0}), 3);
     
     simulator.startSim ();
       
  }
  
  
  Simulator simulator;
  std::unique_ptr<SimData> data;

  std::vector<std::unique_ptr<SimData>>  storage;
};

static GlobalState gstate{};


void Simulator::startSim () {
    
    gstate.data.reset(new SimData{.time = startTime, .state =  Covid::World::State{model}, .stats = Statistics{}});
    
    for (auto& sys : systems) {
      sys->initialise(gstate.data->state, gstate.data->time);
    }
    
    
  }



//Upppaal Sim API  
extern "C" {  
  void initialise_simulation () {
    gstate.simulator.startSim ();
  }

  void step () {
    gstate.simulator.stepSim (*gstate.data);
  }

  std::size_t S () {return  gstate.data->stats.currentS;}
  std::size_t E () {return  gstate.data->stats.currentE;}
  std::size_t I () {return  gstate.data->stats.currentI;}
  std::size_t R () {return  gstate.data->stats.currentR;}
  std::size_t H () {return  gstate.data->stats.currentH;}
  std::size_t V () {return  gstate.data->stats.currentV;}
  
  
}



//Upppaal Splitting API  
extern "C" {  
  int32_t uppaal_store_state () {
    auto val = gstate.storage.size ();
    gstate.storage.push_back (std::make_unique<SimData> (*gstate.data));
    return val;
  }

  //return 0 if fail, 1 if success
  int32_t uppaal_recall_state (int32_t res) {
    if (res >= gstate.storage.size () || res < 0)
      return 0;
    
    gstate.data = std::make_unique<SimData> (*gstate.storage.at (res));
    
    return 1;
  }

  void uppaal_reset (void) {
    gstate.storage.clear ();
    gstate.simulator.startSim ();
  }
  
  /*void step () {
    gstate.simulator.stepSim (*gstate.data);
  }

  std::size_t S () {return  data->currentS;}
  std::size_t E () {return  data->currentE;}
  std::size_t I () {return  data->currentI;}
  std::size_t R () {return  data->currentR;}
  std::size_t H () {return  data->currentH;}
  */
  
}


void SEIRCounter::recvMessage(const Covid::Messaging::Message& m)
{
  auto& data = gstate.data->stats;
  if (m.type == Covid::Messaging::MessageType::InitHealth ||
      m.type == Covid::Messaging::MessageType::HealthChange) {
    
    switch (m.data.healthdata.nstate) {
    case Covid::World::Status::Susceptible:  data.currentS++; break;
    case Covid::World::Status::Exposed: data.currentE++; break;
    case Covid::World::Status::Infectious: data.currentI++; break;
    case Covid::World::Status::Recovered: data.currentR++; break;
    case Covid::World::Status::Vaccinated: data.currentV++; break;
    case Covid::World::Status::Hospitalised: data.currentH++; break;
    }
    
    if (m.type == Covid::Messaging::MessageType::HealthChange) {
      switch (m.data.healthdata.ostate) {
      case Covid::World::Status::Susceptible: data.currentS--; break;
      case Covid::World::Status::Exposed: data.currentE--; break;
      case Covid::World::Status::Infectious: data.currentI--; break;
      case Covid::World::Status::Recovered: data.currentR--; break;
      case Covid::World::Status::Vaccinated: data.currentV--; break;
      case Covid::World::Status::Hospitalised: data.currentH--; break;
      }
    }
  }
}
