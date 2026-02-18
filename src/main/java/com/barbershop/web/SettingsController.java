package com.barbershop.web;

import com.barbershop.domain.EmailMode;
import com.barbershop.service.SettingsService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/settings")
public class SettingsController {

    private final SettingsService settingsService;

    public SettingsController(SettingsService settingsService) {
        this.settingsService = settingsService;
    }

    @GetMapping
    public String settings(Model model) {
        model.addAttribute("emailModes", EmailMode.values());
        model.addAttribute("emailMode", settingsService.getEmailMode().name());
        model.addAttribute("emailFrom", settingsService.getEmailFrom());
        model.addAttribute("targetCm", settingsService.getEstimatorTargetCm());
        model.addAttribute("baseRate", settingsService.getEstimatorBaseRate());
        return "settings/form";
    }

    @PostMapping
    public String save(@RequestParam String emailMode,
                       @RequestParam String emailFrom,
                       @RequestParam String targetCm,
                       @RequestParam String baseRate,
                       RedirectAttributes redirectAttributes) {
        settingsService.set(SettingsService.EMAIL_MODE, emailMode);
        settingsService.set(SettingsService.EMAIL_FROM, emailFrom);
        settingsService.set(SettingsService.EST_TARGET_CM, targetCm);
        settingsService.set(SettingsService.EST_BASE_RATE, baseRate);
        redirectAttributes.addFlashAttribute("success", "Configurações atualizadas.");
        return "redirect:/settings";
    }
}
