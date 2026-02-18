package com.barbershop.web;

import com.barbershop.domain.Plan;
import com.barbershop.domain.PlanDayRule;
import com.barbershop.repo.PlanRepository;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/plans")
public class PlanController {

    private final PlanRepository planRepository;

    public PlanController(PlanRepository planRepository) {
        this.planRepository = planRepository;
    }

    @GetMapping
    public String list(Model model) {
        model.addAttribute("plans", planRepository.findAll());
        return "plans/list";
    }

    @GetMapping("/new")
    public String newForm(Model model) {
        model.addAttribute("plan", new Plan());
        model.addAttribute("rules", PlanDayRule.values());
        return "plans/form";
    }

    @PostMapping
    public String save(@Valid @ModelAttribute Plan plan, BindingResult bindingResult, Model model, RedirectAttributes redirectAttributes) {
        if (bindingResult.hasErrors()) {
            model.addAttribute("rules", PlanDayRule.values());
            return "plans/form";
        }
        planRepository.save(plan);
        redirectAttributes.addFlashAttribute("success", "Plano salvo com sucesso.");
        return "redirect:/plans";
    }

    @GetMapping("/{id}/edit")
    public String edit(@PathVariable Long id, Model model) {
        model.addAttribute("plan", planRepository.findById(id).orElseThrow());
        model.addAttribute("rules", PlanDayRule.values());
        return "plans/form";
    }

    @PostMapping("/{id}/delete")
    public String delete(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        planRepository.deleteById(id);
        redirectAttributes.addFlashAttribute("success", "Plano removido.");
        return "redirect:/plans";
    }
}
