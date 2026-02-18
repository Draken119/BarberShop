package com.barbershop.service;

import com.barbershop.domain.*;
import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.SubscriptionRepository;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.*;

class PlanPolicyServiceTest {

    @Test
    void shouldBlockWeekendForWeekdaysPlan() {
        SubscriptionRepository subscriptionRepository = mock(SubscriptionRepository.class);
        AppointmentRepository appointmentRepository = mock(AppointmentRepository.class);
        PlanPolicyService service = new PlanPolicyService(subscriptionRepository, appointmentRepository);

        Client client = new Client();
        client.setId(1L);
        Plan plan = new Plan();
        plan.setDayRule(PlanDayRule.WEEKDAYS_ONLY);
        plan.setWeeklyLimit(999);
        plan.setMinDaysBetweenAppointments(0);
        Subscription subscription = new Subscription();
        subscription.setPlan(plan);
        when(subscriptionRepository.findByClientAndActiveTrue(client)).thenReturn(Optional.of(subscription));

        assertThrows(IllegalArgumentException.class,
                () -> service.validateAppointment(client, LocalDateTime.of(2026, 2, 21, 10, 0)));
    }

    @Test
    void shouldBlockWhenWeeklyLimitReached() {
        SubscriptionRepository subscriptionRepository = mock(SubscriptionRepository.class);
        AppointmentRepository appointmentRepository = mock(AppointmentRepository.class);
        PlanPolicyService service = new PlanPolicyService(subscriptionRepository, appointmentRepository);

        Client client = new Client();
        client.setId(2L);
        Plan plan = new Plan();
        plan.setDayRule(PlanDayRule.ANY_DAY);
        plan.setWeeklyLimit(1);
        plan.setMinDaysBetweenAppointments(0);
        Subscription subscription = new Subscription();
        subscription.setPlan(plan);
        when(subscriptionRepository.findByClientAndActiveTrue(client)).thenReturn(Optional.of(subscription));
        when(appointmentRepository.countByClientAndStatusAndAppointmentDateTimeBetween(any(), any(), any(), any())).thenReturn(1L);

        assertThrows(IllegalArgumentException.class,
                () -> service.validateAppointment(client, LocalDateTime.of(2026, 2, 18, 10, 0)));
    }
}
