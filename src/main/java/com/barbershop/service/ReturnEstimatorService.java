package com.barbershop.service;

import com.barbershop.domain.Appointment;
import com.barbershop.domain.AppointmentStatus;
import com.barbershop.domain.Client;
import com.barbershop.repo.AppointmentRepository;
import org.springframework.stereotype.Service;

import java.time.temporal.ChronoUnit;
import java.util.Comparator;
import java.util.List;
import java.util.stream.IntStream;

@Service
public class ReturnEstimatorService {

    private final AppointmentRepository appointmentRepository;
    private final SettingsService settingsService;

    public ReturnEstimatorService(AppointmentRepository appointmentRepository, SettingsService settingsService) {
        this.appointmentRepository = appointmentRepository;
        this.settingsService = settingsService;
    }

    public EstimateRange estimateFor(Client client) {
        double targetCm = settingsService.getEstimatorTargetCm();
        double baseRate = adjustedRateByAge(settingsService.getEstimatorBaseRate(), client.getAge());
        int baselineDays = Math.max(5, (int) Math.round(targetCm / baseRate));
        int min = Math.max(3, baselineDays - 3);
        int max = baselineDays + 4;

        List<Appointment> done = appointmentRepository
                .findByClientAndStatusOrderByAppointmentDateTimeAsc(client, AppointmentStatus.DONE);

        if (done.size() >= 3) {
            List<Long> gaps = IntStream.range(1, done.size())
                    .mapToObj(i -> ChronoUnit.DAYS.between(done.get(i - 1).getAppointmentDateTime().toLocalDate(), done.get(i).getAppointmentDateTime().toLocalDate()))
                    .toList();
            double movingAverage = gaps.stream().mapToLong(Long::longValue).average().orElse(baselineDays);
            min = (int) Math.max(3, Math.round((baselineDays + movingAverage) / 2.0) - 2);
            max = (int) Math.max(min + 1, Math.round((baselineDays + movingAverage) / 2.0) + 3);
            return new EstimateRange(min, max, "Heurística de idade + média móvel do histórico real.");
        }

        return new EstimateRange(min, max, "Heurística por idade e taxa média de crescimento.");
    }

    private double adjustedRateByAge(double baseRate, Integer age) {
        if (age == null) {
            return baseRate;
        }
        if (age < 18) {
            return baseRate * 1.10;
        }
        if (age <= 45) {
            return baseRate;
        }
        return baseRate * 0.9;
    }
}
