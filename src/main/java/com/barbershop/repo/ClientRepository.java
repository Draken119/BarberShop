package com.barbershop.repo;

import com.barbershop.domain.Client;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ClientRepository extends JpaRepository<Client, Long> {
    List<Client> findByFullNameContainingIgnoreCaseOrEmailContainingIgnoreCase(String name, String email);
}
