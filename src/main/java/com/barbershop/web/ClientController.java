package com.barbershop.web;

import com.barbershop.domain.Client;
import com.barbershop.domain.Plan;
import com.barbershop.domain.Subscription;
import com.barbershop.repo.AppointmentRepository;
import com.barbershop.repo.ClientRepository;
import com.barbershop.repo.PlanRepository;
import com.barbershop.repo.SubscriptionRepository;
import com.barbershop.service.EmailService;
import com.barbershop.service.EstimateRange;
import com.barbershop.service.ReturnEstimatorService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.LocalDate;

@Controller
@RequestMapping("/clients")
public class ClientController {

    private final ClientRepository clientRepository;
    private final EmailService emailService;
    private final AppointmentRepository appointmentRepository;
    private final ReturnEstimatorService returnEstimatorService;
    private final PlanRepository planRepository;
    private final SubscriptionRepository subscriptionRepository;

    public ClientController(ClientRepository clientRepository, EmailService emailService, AppointmentRepository appointmentRepository, ReturnEstimatorService returnEstimatorService, PlanRepository planRepository, SubscriptionRepository subscriptionRepository) {
        this.clientRepository = clientRepository;
        this.emailService = emailService;
        this.appointmentRepository = appointmentRepository;
        this.returnEstimatorService = returnEstimatorService;
        this.planRepository = planRepository;
        this.subscriptionRepository = subscriptionRepository;
    }

    @GetMapping
    public String list(@RequestParam(required = false) String q, Model model) {
        model.addAttribute("clients", (q == null || q.isBlank()) ? clientRepository.findAll() :
                clientRepository.findByFullNameContainingIgnoreCaseOrEmailContainingIgnoreCase(q, q));
        model.addAttribute("q", q);
        return "clients/list";
    }

    @GetMapping("/new")
    public String createForm(Model model) {
        model.addAttribute("client", new Client());
        return "clients/form";
    }

    @PostMapping
    public String save(@Valid @ModelAttribute Client client, BindingResult bindingResult, RedirectAttributes redirectAttributes) {
        if (bindingResult.hasErrors()) {
            return "clients/form";
        }
        boolean isNew = client.getId() == null;
        Client saved = clientRepository.save(client);
        if (isNew) {
            emailService.sendWelcomeEmail(saved.getEmail(), saved.getFullName());
            redirectAttributes.addFlashAttribute("success", "Cliente criado e e-mail de boas-vindas enviado.");
        } else {
            redirectAttributes.addFlashAttribute("success", "Cliente atualizado com sucesso.");
        }
        return "redirect:/clients";
    }

    @GetMapping("/{id}")
    public String details(@PathVariable Long id, Model model) {
        Client client = clientRepository.findById(id).orElseThrow();
        EstimateRange estimateRange = returnEstimatorService.estimateFor(client);
        model.addAttribute("client", client);
        model.addAttribute("appointments", appointmentRepository.findByClientOrderByAppointmentDateTimeDesc(client));
        model.addAttribute("estimate", estimateRange);
        model.addAttribute("plans", planRepository.findAll());
        model.addAttribute("activeSubscription", subscriptionRepository.findByClientAndActiveTrue(client).orElse(null));
        return "clients/details";
    }

    @GetMapping("/{id}/edit")
    public String edit(@PathVariable Long id, Model model) {
        model.addAttribute("client", clientRepository.findById(id).orElseThrow());
        return "clients/form";
    }

    @PostMapping("/{id}/delete")
    public String delete(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        clientRepository.deleteById(id);
        redirectAttributes.addFlashAttribute("success", "Cliente removido.");
        return "redirect:/clients";
    }

    @PostMapping("/{id}/subscription")
    public String activateSubscription(@PathVariable Long id, @RequestParam Long planId, RedirectAttributes redirectAttributes) {
        Client client = clientRepository.findById(id).orElseThrow();
        Plan plan = planRepository.findById(planId).orElseThrow();
        subscriptionRepository.findByClientAndActiveTrue(client).ifPresent(subscription -> {
            subscription.setActive(false);
            subscriptionRepository.save(subscription);
        });
        Subscription newSubscription = new Subscription();
        newSubscription.setClient(client);
        newSubscription.setPlan(plan);
        newSubscription.setStartDate(LocalDate.now());
        newSubscription.setActive(true);
        subscriptionRepository.save(newSubscription);
        redirectAttributes.addFlashAttribute("success", "Plano ativado/trocado com sucesso.");
        return "redirect:/clients/" + id;
    }

    @PostMapping("/{id}/subscription/cancel")
    public String cancelSubscription(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        Client client = clientRepository.findById(id).orElseThrow();
        subscriptionRepository.findByClientAndActiveTrue(client).ifPresent(subscription -> {
            subscription.setActive(false);
            subscriptionRepository.save(subscription);
        });
        redirectAttributes.addFlashAttribute("success", "Assinatura cancelada.");
        return "redirect:/clients/" + id;
    }
}
