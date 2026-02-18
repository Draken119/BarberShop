package com.barbershop.service;

import com.barbershop.domain.AppSetting;
import com.barbershop.domain.EmailMode;
import com.barbershop.repo.AppSettingRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SettingsService {
    public static final String EMAIL_MODE = "email.mode";
    public static final String EMAIL_FROM = "email.from";
    public static final String EST_TARGET_CM = "estimator.targetCm";
    public static final String EST_BASE_RATE = "estimator.baseRateCmPerDay";

    private final AppSettingRepository repository;

    public SettingsService(AppSettingRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public void ensureDefaults() {
        saveIfMissing(EMAIL_MODE, EmailMode.TEST.name());
        saveIfMissing(EMAIL_FROM, "no-reply@barbearia.local");
        saveIfMissing(EST_TARGET_CM, "1.2");
        saveIfMissing(EST_BASE_RATE, "0.04");
    }

    private void saveIfMissing(String key, String value) {
        if (repository.findById(key).isEmpty()) {
            repository.save(new AppSetting(key, value));
        }
    }

    public String get(String key, String defaultValue) {
        return repository.findById(key).map(AppSetting::getSettingValue).orElse(defaultValue);
    }

    @Transactional
    public void set(String key, String value) {
        repository.save(new AppSetting(key, value));
    }

    public EmailMode getEmailMode() {
        return EmailMode.valueOf(get(EMAIL_MODE, EmailMode.TEST.name()));
    }

    public String getEmailFrom() {
        return get(EMAIL_FROM, "no-reply@barbearia.local");
    }

    public double getEstimatorTargetCm() {
        return Double.parseDouble(get(EST_TARGET_CM, "1.2"));
    }

    public double getEstimatorBaseRate() {
        return Double.parseDouble(get(EST_BASE_RATE, "0.04"));
    }
}
