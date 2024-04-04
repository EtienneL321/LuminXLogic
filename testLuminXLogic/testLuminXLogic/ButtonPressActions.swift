//
//  ButtonPressActions.swift
//  testLuminXLogic
//
//  Created by Etienne Lagace on 2024-03-28.
//
//  From SerialCoder.dev

import Foundation
import SwiftUI

struct ButtonPress: ViewModifier {
    var onPress: () -> Void
    var onRelease: () -> Void
    
    func body(content: Content) -> some View {
        content
            .simultaneousGesture(
                DragGesture(minimumDistance: 0)
                    .onChanged({_ in onPress()})
                    .onEnded({_ in onRelease()})
            )
    }
}

extension View {
    func pressEvents(onPress: @escaping (() -> Void), onRelease: @escaping (() -> Void)) -> some View {
        modifier(ButtonPress(onPress: {onPress()}, onRelease: {onRelease()}))
    }
}
