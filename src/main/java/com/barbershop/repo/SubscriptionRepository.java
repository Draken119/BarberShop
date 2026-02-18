package com.barbershop.repo;

import com.barbershop.domain.Client;
import com.barbershop.domain.Subscription;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface SubscriptionRepository extends JpaRepository<Subscription, Long> {
    Optional<Subscription> findByClientAndActiveTrue(Client client);
    long countByActiveTrue();
}
