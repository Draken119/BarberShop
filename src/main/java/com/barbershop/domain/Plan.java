package com.barbershop.domain;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

@Entity
public class Plan {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Nome é obrigatório")
    @Column(unique = true)
    private String name;

    @NotNull(message = "Preço é obrigatório")
    private BigDecimal price;

    @Enumerated(EnumType.STRING)
    @NotNull
    private PlanDayRule dayRule;

    @Min(0)
    private Integer minDaysBetweenAppointments;

    @Min(1)
    private Integer weeklyLimit;

    private boolean active = true;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal price) { this.price = price; }
    public PlanDayRule getDayRule() { return dayRule; }
    public void setDayRule(PlanDayRule dayRule) { this.dayRule = dayRule; }
    public Integer getMinDaysBetweenAppointments() { return minDaysBetweenAppointments; }
    public void setMinDaysBetweenAppointments(Integer minDaysBetweenAppointments) { this.minDaysBetweenAppointments = minDaysBetweenAppointments; }
    public Integer getWeeklyLimit() { return weeklyLimit; }
    public void setWeeklyLimit(Integer weeklyLimit) { this.weeklyLimit = weeklyLimit; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}
