//
//  LightView.swift
//  testLuminXLogic
//
//  Created by Etienne Lagace on 2024-03-28.
//

import SwiftUI
import CoreBluetooth

var powerOn: UInt8 = 1
var powerOff: UInt8 = 0

var modeColourSensing: UInt8 = 0
var modeSunrise: UInt8 = 1
var modeSunset: UInt8 = 2
var modeAnalogous: UInt8 = 3
var modeWhite: UInt8 = 4

var redColour: [Int] = [255,0,0,0]
var greenColour: [UInt8] = [0,255,0,0]
var blueColour: [UInt8] = [0,0,255,0]
var whiteColour: [UInt8] = [0,0,0,255]

struct LightView: View {
    @State var intensityVal: UInt8 = 80
    
    // Store read data
    var powerVal: UInt8
    var modeVal: UInt8
    var colourVal: [UInt8]
    var intensityProxy: Binding<Double>{
            Binding<Double>(get: {
                //returns the score as a Double
                return Double(intensityVal)
            }, set: {
                //rounds the double to an Int
                print($0.description)
                intensityVal = UInt8($0)
            })
        }
    
    @State var data: CBPeripheral
    var powerControlCharacteristic: CBCharacteristic?
    var modeControlCharacteristic: CBCharacteristic?
    var intensityCharacteristic: CBCharacteristic?
    var rgbwColourCharacteristic: CBCharacteristic?
        
    var disconnect: (_ peripheral: CBPeripheral) -> Void
    var connect: (_ peripheral: CBPeripheral) -> Void
    
    var body: some View {
        VStack {
            Text("Name: \(data.name ?? "Unknown")")
                .font(.title)
            if data.state.rawValue == 2 || data.state.rawValue == 1 {
                Text("State: Connected")
                
                if let intensityCharac = intensityCharacteristic {
                    VStack {
                        Slider(value: intensityProxy,
                               in: 1...100)
                        .padding()
                        Text("power: \(powerVal)  -  mode: \(modeVal)  -  intensity: \(intensityVal)%")
                            .onChange(of:intensityVal) {data.writeValue(Data(bytes: &intensityVal, count: MemoryLayout.size(ofValue: intensityVal)), for: intensityCharac, type: .withResponse)}
                        Text("colour: \(colourVal)")
                        
                    }
                }
                List {
                    if let powerCharac = powerControlCharacteristic {
                        Button(action: {data.writeValue(Data(bytes: &powerOn, count: MemoryLayout.size(ofValue: powerOn)), for: powerCharac, type: .withResponse)}, label: {Text("Power on")})
                        Button(action: {data.writeValue(Data(bytes: &powerOff, count: MemoryLayout.size(ofValue: powerOff)), for: powerCharac, type: .withResponse)}, label: {Text("Power off")})
                    }
                    if let modeCharac = modeControlCharacteristic {
                        Button(action: {data.writeValue(Data(bytes: &modeColourSensing, count: MemoryLayout.size(ofValue: modeColourSensing)), for: modeCharac, type: .withResponse)}, label: {Text("Colour Sensing Mode")})
                        Button(action: {data.writeValue(Data(bytes: &modeSunrise, count: MemoryLayout.size(ofValue: modeSunrise)), for: modeCharac, type: .withResponse)}, label: {Text("Sunrise Mode")})
                        Button(action: {data.writeValue(Data(bytes: &modeSunset, count: MemoryLayout.size(ofValue: modeSunset)), for: modeCharac, type: .withResponse)}, label: {Text("Sunset Mode")})
                        Button(action: {data.writeValue(Data(bytes: &modeAnalogous, count: MemoryLayout.size(ofValue: modeAnalogous)), for: modeCharac, type: .withResponse)}, label: {Text("Analogous Mode")})
                        Button(action: {data.writeValue(Data(bytes: &modeWhite, count: MemoryLayout.size(ofValue: modeWhite)), for: modeCharac, type: .withResponse)}, label: {Text("White Mode")})
                    }
                    if let colourCharac = rgbwColourCharacteristic {
                        Button(action: {data.writeValue(Data(bytes: &redColour, count: MemoryLayout.size(ofValue: modeColourSensing)), for: colourCharac, type: .withResponse)}, label: {Text("Red Colour")})
                    }
                    if let power = powerControlCharacteristic, let mode = modeControlCharacteristic, let colour = rgbwColourCharacteristic, let intensity = intensityCharacteristic {
                        Button(action: {data.readValue(for: power); data.readValue(for: mode); data.readValue(for: colour); data.readValue(for: intensity)}, label: {Text("Read all values")})
                    }
                }
            } else {
                Text("State: Disconnected")
            }
            HStack {
                Button(action: {disconnect(data)}, label: {Text("Disconnect")})
                    .padding()
                    .foregroundColor(.red)
                    .onChange(of:data) {disconnect(data)}
                Button(action: {connect(data)}, label: {Text("Connect")})
                    .padding()
                    .foregroundColor(/*@START_MENU_TOKEN@*/.blue/*@END_MENU_TOKEN@*/)
//                    .onChange(of:data) {connect(data)}
            }
        }
    }
}

// #Preview {
//     LightView()
// }
