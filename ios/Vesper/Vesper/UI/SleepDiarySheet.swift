//  SleepDiarySheet.swift
//  Vesper — the morning sleep-diary check-in. Log last night in a few taps; it
//  feeds the CBT-I sleep-window plan (CBTI.swift). Times of day only — the diary
//  math handles the wrap past midnight.

import SwiftUI

struct SleepDiarySheet: View {
    @Environment(\.dismiss) private var dismiss

    @State private var inBed = SleepDiarySheet.defaultTime(22, 45)
    @State private var tried = SleepDiarySheet.defaultTime(23, 0)
    @State private var onset = 20
    @State private var awakenings = 1
    @State private var waso = 15
    @State private var finalWake = SleepDiarySheet.defaultTime(6, 30)
    @State private var outOfBed = SleepDiarySheet.defaultTime(6, 45)
    @State private var quality = 3

    var body: some View {
        NavigationStack {
            Form {
                Section("Last night") {
                    DatePicker("Got into bed", selection: $inBed, displayedComponents: .hourAndMinute)
                    DatePicker("Tried to sleep", selection: $tried, displayedComponents: .hourAndMinute)
                    stepperRow("Minutes to fall asleep", $onset, 0, 180, 5)
                }
                Section("During the night") {
                    stepperRow("Times you woke", $awakenings, 0, 20, 1)
                    stepperRow("Minutes awake in the night", $waso, 0, 300, 5)
                }
                Section("This morning") {
                    DatePicker("Final wake-up", selection: $finalWake, displayedComponents: .hourAndMinute)
                    DatePicker("Got out of bed", selection: $outOfBed, displayedComponents: .hourAndMinute)
                }
                Section("How rested do you feel?") {
                    Picker("Quality", selection: $quality) {
                        ForEach(1...5, id: \.self) { Text("\($0)").tag($0) }
                    }.pickerStyle(.segmented)
                }
                Section {
                    let e = preview
                    Text(String(format: "Time in bed %.0fh %02.0fm · slept %.0fh %02.0fm · efficiency %d%%",
                                e.timeInBed / 60, e.timeInBed.truncatingRemainder(dividingBy: 60),
                                e.totalSleep / 60, e.totalSleep.truncatingRemainder(dividingBy: 60),
                                Int((e.efficiency * 100).rounded())))
                        .font(.system(size: 12)).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Sleep diary")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { SleepDiary.save(preview); dismiss() }
                }
            }
            .tint(Theme.accent)
        }
        .preferredColorScheme(.dark)
    }

    private var preview: DiaryEntry {
        DiaryEntry(day: SleepDiary.today(Date()), inBedAt: inBed, triedAt: tried,
                   sleepOnsetMins: onset, awakenings: awakenings, wasoMins: waso,
                   finalWakeAt: finalWake, outOfBedAt: outOfBed, quality: quality, note: "")
    }

    private func stepperRow(_ label: String, _ value: Binding<Int>,
                            _ lo: Int, _ hi: Int, _ step: Int) -> some View {
        Stepper(value: value, in: lo...hi, step: step) {
            HStack { Text(label); Spacer()
                Text("\(value.wrappedValue)").foregroundStyle(.secondary) }
        }
    }

    static func defaultTime(_ h: Int, _ m: Int) -> Date {
        Calendar.current.date(bySettingHour: h, minute: m, second: 0, of: Date()) ?? Date()
    }
}
