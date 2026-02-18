package com.barbershop.service;

import com.barbershop.domain.*;
import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.SubscriptionRepository;
import org.springframework.stereotype.Service;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Service
public class PlanPolicyService {

    private final SubscriptionRepository subscriptionRepository;
    private final AppointmentRepository appointmentRepository;

    public PlanPolicyService(SubscriptionRepository subscriptionRepository, AppointmentRepository appointmentRepository) {
        this.subscriptionRepository = subscriptionRepository;
        this.appointmentRepository = appointmentRepository;
    }

    public void validateAppointment(Client client, LocalDateTime when) {
        Subscription subscription = subscriptionRepository.findByClientAndActiveTrue(client)
                .orElseThrow(() -> new IllegalArgumentException("Cliente sem plano ativo."));
        Plan plan = subscription.getPlan();
        validateDayRule(plan, when.toLocalDate().getDayOfWeek());
        validateWeeklyLimit(client, plan, when);
        validateMinDaysBetween(client, plan, when);
    }

    void validateDayRule(Plan plan, DayOfWeek dayOfWeek) {
        if (plan.getDayRule() == PlanDayRule.WEEKDAYS_ONLY &&
                (dayOfWeek == DayOfWeek.SATURDAY || dayOfWeek == DayOfWeek.SUNDAY)) {
            throw new IllegalArgumentException("Este plano permite somente dias úteis.");
        }
    }

    void validateWeeklyLimit(Client client, Plan plan, LocalDateTime when) {
        LocalDate base = when.toLocalDate();
        LocalDate startDate = base.minusDays(base.getDayOfWeek().getValue() - 1L);
        LocalDate endDate = startDate.plusDays(6);
        long count = appointmentRepository.countByClientAndStatusAndAppointmentDateTimeBetween(
                client,
                AppointmentStatus.SCHEDULED,
                startDate.atStartOfDay(),
                endDate.atTime(23, 59, 59)
        );
        if (count >= plan.getWeeklyLimit()) {
            throw new IllegalArgumentException("Limite semanal do plano atingido.");
        }
    }

    void validateMinDaysBetween(Client client, Plan plan, LocalDateTime when) {
        appointmentRepository.findTopByClientAndStatusOrderByAppointmentDateTimeDesc(client, AppointmentStatus.DONE)
                .ifPresent(lastDone -> {
                    long days = java.time.temporal.ChronoUnit.DAYS.between(lastDone.getAppointmentDateTime().toLocalDate(), when.toLocalDate());
                    if (days < plan.getMinDaysBetweenAppointments()) {
                        throw new IllegalArgumentException("Intervalo mínimo entre cortes não respeitado.");
                    }
                });
    }
}
