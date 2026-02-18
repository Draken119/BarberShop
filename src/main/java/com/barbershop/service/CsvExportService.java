package com.barbershop.service;

import com.barbershop.domain.Appointment;
import com.barbershop.domain.Client;
import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.ClientRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class CsvExportService {
    private final ClientRepository clientRepository;
    private final AppointmentRepository appointmentRepository;

    public CsvExportService(ClientRepository clientRepository, AppointmentRepository appointmentRepository) {
        this.clientRepository = clientRepository;
        this.appointmentRepository = appointmentRepository;
    }

    public String exportClients() {
        List<Client> clients = clientRepository.findAll();
        StringBuilder sb = new StringBuilder("id,nome,email,telefone,idade,observacoes\n");
        for (Client c : clients) {
            sb.append(c.getId()).append(',').append(safe(c.getFullName())).append(',').append(safe(c.getEmail())).append(',')
                    .append(safe(c.getPhone())).append(',').append(c.getAge() == null ? "" : c.getAge()).append(',')
                    .append(safe(c.getNotes())).append('\n');
        }
        return sb.toString();
    }

    public String exportAppointments(LocalDate start, LocalDate end) {
        List<Appointment> appointments = appointmentRepository.findByAppointmentDateTimeBetweenOrderByAppointmentDateTime(
                start.atStartOfDay(), end.atTime(23, 59, 59));
        StringBuilder sb = new StringBuilder("id,cliente,dataHora,servico,status\n");
        for (Appointment a : appointments) {
            sb.append(a.getId()).append(',').append(safe(a.getClient().getFullName())).append(',')
                    .append(a.getAppointmentDateTime()).append(',').append(safe(a.getService())).append(',')
                    .append(a.getStatus()).append('\n');
        }
        return sb.toString();
    }

    private String safe(String value) {
        if (value == null) return "";
        return '"' + value.replace("\"", "'") + '"';
    }
}
