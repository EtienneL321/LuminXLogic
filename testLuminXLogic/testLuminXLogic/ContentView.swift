//
//  ContentView.swift
//  testLuminXLogic
//
//  Created by Etienne Lagace on 2024-03-19.
//

import SwiftUI
import CoreBluetooth

// Wrapper to make the CBPeripheral type identifiable
struct peripheralData: Identifiable {
    var id: UUID
    var peripheral: CBPeripheral
    
    var powerControlCharacteristic: CBCharacteristic?
    var modeControlCharacteristic: CBCharacteristic?
    var rgbwColourCharacteristic: CBCharacteristic?
    var intensityCharacterisitc: CBCharacteristic?
    
    var power: UInt8 = 0
    var mode: UInt8 = 0
    var colour: [UInt8] = [0x00, 0x00, 0x00, 0x00]
    var intensity: UInt8 = 100
}

class BLEViewModel: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    // Scan for peripherals when app is turned on
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            self.centralManager?.scanForPeripherals(withServices: nil)
        }
    }
    
    // Check if a new peripheral is already in our list, if not add it - called as a result of scanForPeripherals()
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi RSSI: NSNumber) {
        if !peripherals.contains(peripheral) {
            // get manufacturer data
            if let testData = advertisementData["kCBAdvDataManufacturerData"] as? NSData {
                // allocate memory to buffer
                let buffer = UnsafeMutableRawPointer.allocate(byteCount: testData.length, alignment: 1)
                testData.getBytes(buffer, length: testData.length)
                
                // check for matching manufacturer data
                if buffer.load(as: UInt16.self) == expectedManufacturerData {
                    print("Success")
                    // These next line will only allow the app to connect to one controller
                    self.centralManager?.stopScan()
                    self.centralManager?.connect(peripheral, options: nil)
                    
                    // get peripheral info
                    self.peripheralList.append(
                        peripheralData(
                            id: peripheral.identifier,
                            peripheral: peripheral
                        )
                    )
                    
                    // store peripheral
                    peripherals.append(peripheral)
                }
                
                // deallocate buffer memory
                buffer.deallocate()
            }
        }
    }
    
    // Discover any services - called as a result of connect()
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("--------- Attempting to discover services ---------")
        self.peripherals[0].discoverServices(nil) //can provide array of specific services
        self.peripherals[0].delegate = self
        
        self.updatePeripheralList()
    }
    
    // Discover any characteristics from discovered services - called as a result of discoverServices()
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        print("--------- Attempting to discover characteristics ---------")
        if let services = peripheral.services{
            for service in services{
                peripheral.discoverCharacteristics(nil, for: service)
            }
        }
        
        self.updatePeripheralList()
    }
    
    // Read data from BLE packet - called as as a result of discoverCharacteristic()
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        print("--------- Attempting to read characteristics ---------")
        for charac in service.characteristics!{
            peripheral.discoverDescriptors(for: charac)
            
            characteristicData.append(charac)
            
            switch charac.uuid {
            case POWER_CONTROL_CHARACTERISTIC:
                updatePowerControlCharacteristic(characteristic: charac, peripheral: peripheral)
                peripheral.setNotifyValue(true, for: charac)
                peripheral.readValue(for: charac)
            case MODE_CONTROL_CHARACTERISTIC:
                updateModeControlCharacteristic(characteristic: charac, peripheral: peripheral)
                peripheral.setNotifyValue(true, for: charac)
                peripheral.readValue(for: charac)
            case RGBW_COLOUR_CHARACTERISTIC:
                updateRGBWColourCharacteristic(characteristic: charac, peripheral: peripheral)
                peripheral.setNotifyValue(true, for: charac)
                peripheral.readValue(for: charac)
            case INTENSITY_CHARACTERISTIC:
                updateIntensityCharacteristic(characteristic: charac, peripheral: peripheral)
                peripheral.setNotifyValue(true, for: charac)
                peripheral.readValue(for: charac)
            default:
                print("Characteristic with uuid <\(charac.uuid)> was not recognized")
            }
        }
        
        self.updatePeripheralList()
    }
    
    // Read raw data from formatted BLE packet - called as a result of readValue()
    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard let data = characteristic.value else {
            print("ERROR - \(String(describing: error))")
            return
        }
        switch characteristic.uuid {
        case POWER_CONTROL_CHARACTERISTIC:
            updatePowerControlReadValue(characteristic: characteristic, peripheral: peripheral)
            print("SUCCESSFUL - Read value \(Int(data[0])) from power control characteristic")
        case MODE_CONTROL_CHARACTERISTIC:
            updateModeControlReadValue(characteristic: characteristic, peripheral: peripheral)
            print("SUCCESSFUL - Read value \(Int(data[0])) from mode control characteristic")
        case RGBW_COLOUR_CHARACTERISTIC:
            updateColourReadValue(characteristic: characteristic, peripheral: peripheral)
            print("SUCCESSFUL - Read value [\(Int(data[0])),\(Int(data[1])),\(Int(data[2])),\(Int(data[3]))] from rgbw colour characteristic")
        case INTENSITY_CHARACTERISTIC:
            updateIntensityReadValue(characteristic: characteristic, peripheral: peripheral)
            print("SUCCESSFUL - Read value \(Int(data[0])) from intensity characteristic")
        default:
            print("Characteristic with uuid <\(characteristic.uuid)> was not recognized")
        }
        
        updatePeripheralList()
    }
    
    // Check if write value was successful - called as a result of writeValue() w/ type withResponse
    func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        if error != nil {
            print("Produced Error: \(String(describing: error))")
        } else {
            switch characteristic.uuid {
            case POWER_CONTROL_CHARACTERISTIC:
                print("SUCCESSFUL - Wrote value to power control characteristic")
            case MODE_CONTROL_CHARACTERISTIC:
                print("SUCCESSFUL - Wrote value to mode control characteristic")
            case RGBW_COLOUR_CHARACTERISTIC:
                print("SUCCESSFUL - Wrote value to rgbw colour characteristic")
            case INTENSITY_CHARACTERISTIC:
                print("SUCCESSFUL - Wrote value to intensity characteristic")
            default:
                print("Characteristic with uuid <\(characteristic.uuid)> was not recognized")
            }
        }
    }
    
    // Quick function to copy over data from a CBPeripheral type to a Data type. This is important
    // to be able to use elements like List that require a Data parameter.
    func updatePeripheralList() {
        for i in 0...(peripherals.count - 1) {
            peripheralList[i].peripheral = peripherals[i]
        }
    }
    func updatePowerControlCharacteristic(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                peripheralList[i].powerControlCharacteristic = characteristic
            }
        }
    }
    func updateModeControlCharacteristic(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                peripheralList[i].modeControlCharacteristic = characteristic
            }
        }
    }
    func updateRGBWColourCharacteristic(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                peripheralList[i].rgbwColourCharacteristic = characteristic
            }
        }
    }
    func updateIntensityCharacteristic(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                peripheralList[i].intensityCharacterisitc = characteristic
            }
        }
    }
    func updatePowerControlReadValue(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                if let data = characteristic.value {
                    peripheralList[i].power = UInt8(data[0])
                }
            }
        }
    }
    func updateModeControlReadValue(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                if let data = characteristic.value {
                    peripheralList[i].mode = UInt8(data[0])
                }
            }
        }
    }
    func updateColourReadValue(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                if let data = characteristic.value {
                    peripheralList[i].colour[0] = (UInt8(data[0]))
                    peripheralList[i].colour[1] = (UInt8(data[1]))
                    peripheralList[i].colour[2] = (UInt8(data[2]))
                    peripheralList[i].colour[3] = (UInt8(data[3]))
                } else {
                    print("ERROR - Colour was not read")
                }
            }
        }
    }
    func updateIntensityReadValue(characteristic: CBCharacteristic, peripheral: CBPeripheral) {
        for i in 0...(peripherals.count - 1) {
            if peripheralList[i].id == peripheral.identifier {
                if let data = characteristic.value {
                    peripheralList[i].intensity = UInt8(data[0])
                }
            }
        }
    }
    
    // This is the central manager, it is the first key step
    private var centralManager: CBCentralManager?
    
    // This list will store the peripherals we find
    var peripherals: [CBPeripheral] = []
    
    // This list will store the names of the peripherals we find
    @Published var peripheralList: [peripheralData] = []
    
    var characteristicData: [CBCharacteristic] = []
    
    // Constant global class variables
    let expectedManufacturerData: UInt16 = 0xDDDD
    // List of discoverable services
    let discoverableServices: [CBUUID] = [
        CBUUID(string: "0x7c4d8001-0013-0012-0011-7c4d80010001"),
        CBUUID(string: "0x7c4d8001-0013-0012-0011-7c4d80010002")]
    
    let POWER_CONTROL_CHARACTERISTIC = CBUUID(string: "7c4d8002-0013-0012-0011-7c4d00010001")
    let MODE_CONTROL_CHARACTERISTIC = CBUUID(string: "7c4d8002-0013-0012-0011-7c4d00010002")
    let RGBW_COLOUR_CHARACTERISTIC = CBUUID(string: "0x7c4d8002-0013-0012-0011-7c4d00020005")
    let INTENSITY_CHARACTERISTIC = CBUUID(string: "0x7c4d8002-0013-0012-0011-7c4d00020006")
    
    override init() {
        super.init()
        
        // Assign delegate to self to get central manager to work
        self.centralManager = CBCentralManager(delegate: self, queue: .main)
    }
}

struct ContentView: View {
    @ObservedObject private var bleViewModel = BLEViewModel()
    
    var body: some View {
        NavigationStack {
            NavigationView {
                List(bleViewModel.peripheralList) { peripheral in
                    NavigationLink(
                        destination: {LightView(
                            intensityVal: peripheral.intensity,
                            powerVal: peripheral.power,
                            modeVal: peripheral.mode,
                            colourVal: peripheral.colour,
                            data: peripheral.peripheral,
                            powerControlCharacteristic: peripheral.powerControlCharacteristic,
                            modeControlCharacteristic: peripheral.modeControlCharacteristic,
                            intensityCharacteristic: peripheral.intensityCharacterisitc,
                            rgbwColourCharacteristic: peripheral.rgbwColourCharacteristic)},
                        label: {Text("Name - \(peripheral.peripheral.name ?? "Unknown")")})
                }
                .navigationTitle("Peripherals")
                .listRowSpacing(8)
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .padding()
            VStack {
                Image(systemName: "scribble.variable")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                Text("Hello, world!")
                Button(action: {print("button click")}, label: {
                    Text("BLE Device")
                })
                .padding(.all)
                .frame(width: 250.0)
                .border(Color.black)
                List {
                    
                }
                .foregroundStyle(Color.green)
                .listRowSpacing(8)
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .padding()
        }
    }
}

#Preview {
    ContentView()
}
