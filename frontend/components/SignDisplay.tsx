import React, { useEffect, useRef, useState } from "react";
import { TouchableOpacity, Text, StyleSheet, View, Image } from "react-native";
import { ProhibitorySign, MandatorySign, DangerSign, OtherSign, TrafficSign } from "../constants/Types"
import { MandatorySignsSet, DangerSignsSet, ProhibitorySignsSet, OtherSignsSet } from "@/constants/Signs";
import images from "@/constants/images";

interface SignDisplayProps {
    inputArray: string[];
}

const SignDisplay: React.FC<SignDisplayProps> = ({inputArray}) => {
    
    const [mandatorySigns, setMandatorySigns] = useState<[string]>(['']);
    const [dangerSigns, setDangerSigns] = useState<[string]>(['']);
    const [otherSigns, setOtherSigns] = useState<[string]>(['']);
    const [prohibitorySigns, setProhibitorySigns] = useState<string[]>(['', '']);

    const handleProhibitorySigns = (sign: string) => {
        if (sign.includes("speed limit")) {
            setProhibitorySigns(prev => [sign, prev[1]]); 
            return;
        }
        if (sign.includes("no overtaking")) {
            setProhibitorySigns(prev => [prev[0], sign]); 
            return;
        }
        if (sign.includes("restriction")) {
            switch (sign) {
                case "restriction ends":
                    setProhibitorySigns(['', '']);
                    return;
                case "restriction ends (overtaking)":
                    setProhibitorySigns(prev => [prev[0], '']);
                    return;
                case "restriction ends 80":
                    setProhibitorySigns(prev => ['', prev[1]]);
                    return;
                case "restriction ends (overtaking (trucks))":
                    setProhibitorySigns(prev => [prev[0], '']);
                    return;
                default:
                    return;
            }
        }
    };

    useEffect(() => {
        inputArray.forEach(element => {
            if (ProhibitorySignsSet.has(element as ProhibitorySign)) {
                handleProhibitorySigns(element);
            }
            if (MandatorySignsSet.has(element as MandatorySign)) {
                setMandatorySigns([element])
            }
            if (DangerSignsSet.has(element as DangerSign)) {
                setDangerSigns([element])
            } 
            if (OtherSignsSet.has(element as OtherSign)) {
                setOtherSigns([element])
            } 
            
        });

        if (!inputArray.some(sign => DangerSignsSet.has(sign as DangerSign))) {
            setDangerSigns(['']);
        }
        if (!inputArray.some(sign => MandatorySignsSet.has(sign as MandatorySign))) {
            setMandatorySigns(['']);
        }
        if (!inputArray.some(sign => OtherSignsSet.has(sign as OtherSign))) {
            setOtherSigns(['']);
        }
    }, [inputArray]);

    return (
        <View style={styles.container}>
            <View style={styles.box1}>
                {prohibitorySigns.map((sign, index) => (
                    sign ? (
                        <Image 
                            key={index} 
                            source={images[sign as keyof typeof images]} 
                            style={styles.image} 
                        />
                    ) : null
                ))}
            </View>
            <View style={styles.box1}>
                {dangerSigns.map((sign, index) => (
                    sign ? (
                        <Image 
                            key={index} 
                            source={images[sign as keyof typeof images]} 
                            style={styles.image} 
                        />
                    ) : null
                ))}
            </View>
            <View style={styles.box1}>
                {mandatorySigns.map((sign, index) => (
                    sign ? (
                        <Image 
                            key={index} 
                            source={images[sign as keyof typeof images]} 
                            style={styles.image} 
                        />
                    ) : null
                ))}
            </View>
            <View style={styles.box1}>
                {otherSigns.map((sign, index) => (
                    sign ? (
                        <Image 
                            key={index} 
                            source={images[sign as keyof typeof images]} 
                            style={styles.image} 
                        />
                    ) : null
                ))}
            </View>
        </View>
    );
};



const styles = StyleSheet.create({
  button: {
    backgroundColor: "#3498db",
    padding: 10,
    borderRadius: 5,
    alignItems: "center",
  },
  text: {
    color: "black",
    fontSize: 16,
  },
  container: {
    flex: 1, 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    padding: 20,
    backgroundColor: '#f8f9fb'
  },
  box1: {
    backgroundColor: 'white',
  },
  image: {
    width: 80,
    height: 80,
    resizeMode: 'contain',
  },
});

export default SignDisplay;
