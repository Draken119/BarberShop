package com.barbershop.service;

import com.barbershop.domain.EmailMode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    private static final Logger log = LoggerFactory.getLogger(EmailService.class);
    private final JavaMailSender mailSender;
    private final SettingsService settingsService;

    public EmailService(JavaMailSender mailSender, SettingsService settingsService) {
        this.mailSender = mailSender;
        this.settingsService = settingsService;
    }

    public void sendWelcomeEmail(String to, String name) {
        String subject = "Bem-vindo à Barbearia";
        String body = "Olá %s, seu cadastro foi concluído com sucesso!".formatted(name);
        if (settingsService.getEmailMode() == EmailMode.TEST) {
            log.info("[EMAIL TEST] to={} subject={} body={}", to, subject, body);
            log.warn("[ALERTA] Novo cliente cadastrado: {} ({})", name, to);
            return;
        }
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(settingsService.getEmailFrom());
        message.setTo(to);
        message.setSubject(subject);
        message.setText(body + "\n\nAlerta: não esqueça de agendar seu primeiro corte.");
        mailSender.send(message);
    }
}
