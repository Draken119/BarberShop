# ===== Build stage (tem Maven) =====
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /app

COPY pom.xml .
# baixa dependências antes (cache melhor)
RUN mvn -q -e -DskipTests dependency:go-offline

COPY . .
RUN mvn -q -DskipTests clean package

# ===== Run stage (mais leve) =====
FROM eclipse-temurin:21-jre
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

# Render usa a variável PORT
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "java -Dserver.port=${PORT} -jar app.jar"]
