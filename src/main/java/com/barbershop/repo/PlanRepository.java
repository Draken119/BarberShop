package com.barbershop.repo;

import com.barbershop.domain.Plan;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PlanRepository extends JpaRepository<Plan, Long> {
    Optional<Plan> findByNameIgnoreCase(String name);
    long countByActiveFalse();
}
