# Imagen de desarrollo del frontend (Vite con recarga en caliente).
# En modo demo el frontend se compila dentro de nginx/Dockerfile.demo.
FROM node:22-alpine AS desarrollo
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
