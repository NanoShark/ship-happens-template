// Add these functions to your existing services/api.js

// Tutorial endpoints
export const getTutorialSteps = async () => {
  try {
    const response = await axios.get(`${API_URL}/tutorials/steps`);
    return response.data;
  } catch (error) {
    console.error('Error fetching tutorial steps:', error);
    throw error;
  }
};

export const getTutorialStep = async (stepId) => {
  try {
    const response = await axios.get(`${API_URL}/tutorials/steps/${stepId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching tutorial step:', error);
    throw error;
  }
};

export const completeStep = async (stepId) => {
  try {
    const response = await axios.post(`${API_URL}/tutorials/steps/${stepId}/complete`);
    return response.data;
  } catch (error) {
    console.error('Error completing step:', error);
    throw error;
  }
};

// Container service endpoints
export const createContainer = async (stepId) => {
  try {
    const response = await axios.post(`${API_URL}/containers/create`, { step_id: stepId });
    return response.data;
  } catch (error) {
    console.error('Error creating container:', error);
    throw error;
  }
};

export const validateSolution = async (sessionId, validationScript) => {
  try {
    const response = await axios.post(`${API_URL}/containers/validate/${sessionId}`, {
      validation_script: validationScript
    });
    return response.data;
  } catch (error) {
    console.error('Error validating solution:', error);
    throw error;
  }
};

export const terminateContainer = async (sessionId) => {
  try {
    const response = await axios.post(`${API_URL}/containers/terminate/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error terminating container:', error);
    throw error;
  }
};