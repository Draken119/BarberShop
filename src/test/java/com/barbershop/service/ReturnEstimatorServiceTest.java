package com.barbershop.service;

import com.barbershop.domain.Appointment;
import com.barbershop.domain.AppointmentStatus;
import com.barbershop.domain.Client;
import com.barbershop.repo.AppointmentRepository;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.*;

class ReturnEstimatorServiceTest {

    @Test
    void shouldUseHeuristicWithoutHistory() {
        AppointmentRepository appointmentRepository = mock(AppointmentRepository.class);
        SettingsService settingsService = mock(SettingsService.class);
        when(settingsService.getEstimatorTargetCm()).thenReturn(1.2);
        when(settingsService.getEstimatorBaseRate()).thenReturn(0.04);

        ReturnEstimatorService service = new ReturnEstimatorService(appointmentRepository, settingsService);
        Client client = new Client();
        client.setId(1L);
        client.setAge(30);
        when(appointmentRepository.findByClientAndStatusOrderByAppointmentDateTimeAsc(client, AppointmentStatus.DONE)).thenReturn(List.of());

        EstimateRange estimate = service.estimateFor(client);

        assertTrue(estimate.minDays() > 0);
        assertTrue(estimate.maxDays() >= estimate.minDays());
    }

    @Test
    void shouldAdjustWithMovingAverageWhenHistoryExists() {
        AppointmentRepository appointmentRepository = mock(AppointmentRepository.class);
        SettingsService settingsService = mock(SettingsService.class);
        when(settingsService.getEstimatorTargetCm()).thenReturn(1.2);
        when(settingsService.getEstimatorBaseRate()).thenReturn(0.04);

        ReturnEstimatorService service = new ReturnEstimatorService(appointmentRepository, settingsService);
        Client client = new Client();
        client.setId(1L);
        client.setAge(30);

        Appointment a1 = appointment(client, LocalDateTime.of(2026, 1, 1, 10, 0));
        Appointment a2 = appointment(client, LocalDateTime.of(2026, 1, 15, 10, 0));
        Appointment a3 = appointment(client, LocalDateTime.of(2026, 1, 29, 10, 0));
        when(appointmentRepository.findByClientAndStatusOrderByAppointmentDateTimeAsc(client, AppointmentStatus.DONE)).thenReturn(List.of(a1, a2, a3));

        EstimateRange estimate = service.estimateFor(client);

        assertTrue(estimate.reasoning().contains("média móvel"));
    }

    private Appointment appointment(Client client, LocalDateTime dateTime) {
        Appointment a = new Appointment();
        a.setClient(client);
        a.setStatus(AppointmentStatus.DONE);
        a.setAppointmentDateTime(dateTime);
        return a;
    }
}
