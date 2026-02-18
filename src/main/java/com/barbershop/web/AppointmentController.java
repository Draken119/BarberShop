package com.barbershop.web;

import com.barbershop.domain.Appointment;
import com.barbershop.domain.AppointmentStatus;
import com.barbershop.domain.Client;
import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.ClientRepository;
import com.barbershop.service.PlanPolicyService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/appointments")
public class AppointmentController {

    private final AppointmentRepository appointmentRepository;
    private final ClientRepository clientRepository;
    private final PlanPolicyService planPolicyService;

    public AppointmentController(AppointmentRepository appointmentRepository, ClientRepository clientRepository, PlanPolicyService planPolicyService) {
        this.appointmentRepository = appointmentRepository;
        this.clientRepository = clientRepository;
        this.planPolicyService = planPolicyService;
    }

    @GetMapping
    public String list(Model model) {
        model.addAttribute("appointments", appointmentRepository.findByAppointmentDateTimeBetweenOrderByAppointmentDateTime(
                java.time.LocalDate.now().minusMonths(3).atStartOfDay(),
                java.time.LocalDate.now().plusMonths(3).atTime(23,59,59)
        ));
        return "appointments/list";
    }

    @GetMapping("/new")
    public String form(Model model) {
        model.addAttribute("appointment", new AppointmentForm());
        fillFormOptions(model);
        return "appointments/form";
    }

    @PostMapping
    public String save(@Valid @ModelAttribute("appointment") AppointmentForm form, BindingResult bindingResult,
                       Model model, RedirectAttributes redirectAttributes) {
        if (bindingResult.hasErrors()) {
            fillFormOptions(model);
            return "appointments/form";
        }
        Client client = clientRepository.findById(form.getClientId()).orElseThrow();
        try {
            planPolicyService.validateAppointment(client, form.getAppointmentDateTime());
            Appointment appointment = new Appointment();
            appointment.setId(form.getId());
            appointment.setClient(client);
            appointment.setAppointmentDateTime(form.getAppointmentDateTime());
            appointment.setService(form.getService());
            appointment.setStatus(form.getStatus());
            appointmentRepository.save(appointment);
            redirectAttributes.addFlashAttribute("success", "Agendamento salvo.");
            return "redirect:/appointments";
        } catch (IllegalArgumentException e) {
            bindingResult.reject("policy", e.getMessage());
            fillFormOptions(model);
            return "appointments/form";
        }
    }

    @GetMapping("/{id}/edit")
    public String edit(@PathVariable Long id, Model model) {
        Appointment appointment = appointmentRepository.findById(id).orElseThrow();
        AppointmentForm form = new AppointmentForm();
        form.setId(appointment.getId());
        form.setClientId(appointment.getClient().getId());
        form.setAppointmentDateTime(appointment.getAppointmentDateTime());
        form.setService(appointment.getService());
        form.setStatus(appointment.getStatus());
        model.addAttribute("appointment", form);
        fillFormOptions(model);
        return "appointments/form";
    }

    @PostMapping("/{id}/delete")
    public String delete(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        appointmentRepository.deleteById(id);
        redirectAttributes.addFlashAttribute("success", "Agendamento removido.");
        return "redirect:/appointments";
    }

    private void fillFormOptions(Model model) {
        model.addAttribute("clients", clientRepository.findAll());
        model.addAttribute("statuses", AppointmentStatus.values());
    }
}
