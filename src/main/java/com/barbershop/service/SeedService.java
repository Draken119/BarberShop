package com.barbershop.service;

import com.barbershop.domain.Plan;
import com.barbershop.domain.PlanDayRule;
import com.barbershop.repo.PlanRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Service
public class SeedService {

    private final PlanRepository planRepository;
    private final SettingsService settingsService;

    public SeedService(PlanRepository planRepository, SettingsService settingsService) {
        this.planRepository = planRepository;
        this.settingsService = settingsService;
    }

    @PostConstruct
    public void initialize() {
        createIfMissing("Basic", BigDecimal.valueOf(79.90), PlanDayRule.ANY_DAY, 7, 1);
        createIfMissing("Plus", BigDecimal.valueOf(119.90), PlanDayRule.WEEKDAYS_ONLY, 0, 999);
        createIfMissing("Max", BigDecimal.valueOf(159.90), PlanDayRule.ANY_DAY, 0, 999);
        settingsService.ensureDefaults();
    }

    private void createIfMissing(String name, BigDecimal price, PlanDayRule rule, int minDays, int weeklyLimit) {
        if (planRepository.findByNameIgnoreCase(name).isPresent()) {
            return;
        }
        Plan plan = new Plan();
        plan.setName(name);
        plan.setPrice(price);
        plan.setDayRule(rule);
        plan.setMinDaysBetweenAppointments(minDays);
        plan.setWeeklyLimit(weeklyLimit);
        planRepository.save(plan);
    }
}
