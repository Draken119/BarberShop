package com.barbershop.service;

import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.ClientRepository;
import com.barbershop.repo.PlanRepository;
import com.barbershop.repo.SubscriptionRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;

@Service
public class DashboardService {
    private final ClientRepository clientRepository;
    private final AppointmentRepository appointmentRepository;
    private final SubscriptionRepository subscriptionRepository;
    private final PlanRepository planRepository;

    public DashboardService(ClientRepository clientRepository, AppointmentRepository appointmentRepository, SubscriptionRepository subscriptionRepository, PlanRepository planRepository) {
        this.clientRepository = clientRepository;
        this.appointmentRepository = appointmentRepository;
        this.subscriptionRepository = subscriptionRepository;
        this.planRepository = planRepository;
    }

    public DashboardView getView() {
        LocalDate today = LocalDate.now();
        long noActivePlan = clientRepository.count() - subscriptionRepository.countByActiveTrue();
        return new DashboardView(
                clientRepository.count(),
                appointmentRepository.countByAppointmentDateTimeBetween(today.atStartOfDay(), today.atTime(23, 59, 59)),
                appointmentRepository.countByAppointmentDateTimeBetween(today.atStartOfDay(), today.plusDays(7).atTime(23, 59, 59)),
                noActivePlan,
                planRepository.countByActiveFalse()
        );
    }

    public record DashboardView(long totalClients, long todayAppointments, long next7DaysAppointments,
                                long clientsWithoutPlan, long inactivePlans) {
    }
}
