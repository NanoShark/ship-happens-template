FROM node:14-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./

# Install dependencies with more detailed error output
RUN npm install 

# Copy the rest of the application
COPY . .

# Expose port 3000 and start the app
EXPOSE 3000
CMD ["npm", "start"]