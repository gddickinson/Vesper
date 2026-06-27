//  Vesper-Bridging-Header.h
//  Copy to Vesper/Vesper-Bridging-Header.h and set
//  Build Settings ▸ "Objective-C Bridging Header" = Vesper/Vesper-Bridging-Header.h
//
//  Exposes the sherpa-onnx C API (used by SherpaOnnx.swift) to Swift.
//  The header path matches sherpa-onnx.xcframework's Headers layout (v1.13.x).

#import "sherpa-onnx/c-api/c-api.h"
