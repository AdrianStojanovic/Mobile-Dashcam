import { ProhibitorySign, MandatorySign, DangerSign, OtherSign, TrafficSign } from "./Types"

export const ProhibitorySignsSet = new Set<ProhibitorySign>([
    "speed limit 20",
    "speed limit 30",
    "speed limit 50",
    "speed limit 60",
    "speed limit 70",
    "speed limit 80",
    "speed limit 100",
    "speed limit 120",
    "no overtaking",
    "no overtaking (trucks)",
    "restriction ends",
    "restriction ends (overtaking)",
    "restriction ends 80",
    "restriction ends (overtaking (trucks))",
  ]);

  export const MandatorySignsSet = new Set<MandatorySign>([
    "go right", "go left", "go straight", "go right or straight", "go left or straight", "keep right", 
    "keep left",
  ]);
  
  export const DangerSignsSet = new Set<DangerSign>([
    "priority at next intersection", "danger", "bend left", "bend right", "bend", "uneven road", "slippery road", 
    "road narrows", "construction", "traffic signal", "pedestrian crossing", "school crossing", "cycles crossing", 
    "snow", "animals"
  ]);
  
  export const OtherSignsSet = new Set<OtherSign>([
    "priority road", "give way", "stop", "no entry", "no trucks", "no traffic both ways", "roundabout"
  ]);