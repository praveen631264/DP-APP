# Stage 1: Build the Angular application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package configuration
COPY package.json ./

# Install dependencies
RUN npm install --network-timeout=600000

# Copy the rest of the application source code
COPY . .

# Build the application for production
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.25-alpine

# Remove the default Nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy the built application from the 'build' stage
COPY --from=build /app/dist/intelli-docs /usr/share/nginx/html

# Copy the Nginx configuration file
COPY ../nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80