//
//  ContentView.swift
//  TestApp
//
//  Created by Etienne Lagace on 2024-04-03.
//

import SwiftUI

struct ContentView: View {
    @State var intensity: Double = 80
//    @State var isEditing = false
    
    @State private var isPlaying: Bool = false
    
    var body: some View {
        VStack {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, world!")
//            Slider(value: intensity, in: 1...100)
            Button(isPlaying ? "pause" : "play") {
                isPlaying.toggle()
            }
            Slider(
                value: $intensity,
                in: 1...100,
                onEditingChanged: {_ in print("worked")})
        }
        .padding()
    }
}

#Preview {
    ContentView()
}
