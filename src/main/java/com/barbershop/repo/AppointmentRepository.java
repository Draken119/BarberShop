package com.barbershop.repo;

import com.barbershop.domain.Appointment;
import com.barbershop.domain.AppointmentStatus;
import com.barbershop.domain.Client;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AppointmentRepository extends JpaRepository<Appointment, Long> {
    long countByAppointmentDateTimeBetween(LocalDateTime start, LocalDateTime end);
    List<Appointment> findByAppointmentDateTimeBetweenOrderByAppointmentDateTime(LocalDateTime start, LocalDateTime end);
    long countByClientAndStatusAndAppointmentDateTimeBetween(Client client, AppointmentStatus status, LocalDateTime start, LocalDateTime end);
    Optional<Appointment> findTopByClientAndStatusOrderByAppointmentDateTimeDesc(Client client, AppointmentStatus status);
    List<Appointment> findByClientOrderByAppointmentDateTimeDesc(Client client);
    List<Appointment> findByClientAndStatusOrderByAppointmentDateTimeAsc(Client client, AppointmentStatus status);
}
