'''This file contains a set of classes for building simple neural networks
   using a modular layer structure. Most of the code is "original" (not
   directly copied) but some of the functions, ideas, and control flow 
   are taken from Michael Nielson's Neural Networks and Deep Learning Book. 
   These include the code for the cost functions, code for the 
   stochastic_gradient_descent() function, and the control flow for the 
   mini_batch_pass() function. Also, the explanations of backpropagation 
   from Nielson's book and Stanford CS231n helped me figure out how to program 
   backpropagation in this code. I also took inspiration from a variety of
   examples I found online including:
   
   https://stackabuse.com/creating-a-neural-network-from-scratch-in-python/
   https://towardsdatascience.com/deep-neural-networks-from-scratch-in-python-451f07999373
   https://towardsai.net/p/machine-learning/nothing-but-numpy-understanding-creating-neural-networks-with-computational-graphs-from-scratch-6299901091b0
   https://towardsdatascience.com/math-neural-network-from-scratch-in-python-d6da9f29ce65.''' 




# import libs
import numpy as np
import random
import matplotlib.pyplot as plt


'''===========================================================================================
   ====================================== LAYER CLASSES ======================================
   ==========================================================================================='''


# ==================================== Fully Connected Layer =================================
# The fully connected layer calculates the weighted sum (the "z" values) of the prior layer's
# activations. It also keeps track of the weights, biases, and partial derivatives.

class FullyConnectedLayer:

    # need to know the number of neurons in this layer and previous layer to form weight matrix
    def __init__(self, layer_size, previous_layer_size):
            self.N = layer_size
            self.N_p = previous_layer_size

            # initialize a small random weight matrix with N rows and N_p columns
            self.W = np.random.randn(self.N, self.N_p)/10

            # empty weight partial derivative matrix
            self.dW = np.zeros((self.N, self.N_p))

            # initialize a small random bias column vector with N rows
            self.B = np.random.randn(self.N,1)/10

            # empty bias partial derivative vector
            self.dB = np.zeros((self.N,1))

            # keep track of a column vector of weighted sums for the layer
            self.Z = np.zeros((self.N,1))

            # keep a running sum for the weights and biases, used for SGD
            self.dW_sum = np.zeros((self.N, self.N_p))
            self.dB_sum = np.zeros((self.N,1))

            # store the previous layer activations for forward/backward prop
            self.previous_layer_activations = np.zeros((previous_layer_size,1))

    # do a (weight matrix)*(activation vector) multiplication to get the weighted sum for the layer
    def forward_propagation(self, previous_layer_activations):
        # check that the matrix multiplication is possible
        if self.W.shape[1] != previous_layer_activations.shape[0]:
            print("mismatch between weight matrix columns and activation rows")
            print(self.W.shape[1],  previous_layer_activations.shape[0])
            exit()
        else:
            # get the weighted sum for this layer
            self.Z = np.dot(self.W, previous_layer_activations) + self.B

            # update the previous layer activations
            self.previous_layer_activations = previous_layer_activations

        # return the weighted sum for the next layer to use    
        return self.Z

    # this calculates the partial derivatives for a backward pass of one training input
    def backward_propagation(self, upstream_gradient):
        # first calculate the partial derivatives for the weights, represents an outer product of two vectors
        self.dW = np.dot(upstream_gradient, self.previous_layer_activations.transpose())
        self.dW_sum += self.dW

        # next set the partial derivatives for the biases to the upstream gradient
        self.dB = upstream_gradient
        self.dB_sum += self.dB

        # dot the local gradient by the upstream and return this as the new upstream gradient
        # this accounts for branching when two downstream gradients merge 
        return np.dot(self.W.transpose(), upstream_gradient)

    # once a mini-batch finishes, adjust the parameters by the average gradient over the mini-batch
    def update_parameters(self, mini_batch_size, eta):
        self.W -= eta*(self.dW_sum / mini_batch_size)
        self.B -= eta*(self.dB_sum / mini_batch_size)

        # reset the sums
        self.dW_sum[:] = 0
        self.dB_sum[:] = 0


# ==================================== Sigmoid Layer =====================================
# the sigmoid layer is a nonlinearity activation function layer that is placed after a 
# fully connected layer

class SigmoidLayer:
    def __init__(self, layer_size):
        self.N = layer_size

        # column vector of activations
        self.activation = np.zeros((self.N,1))
    
    # apply the activation function on the weighted sum
    def forward_propagation(self, weighted_sum):
        self.activation = 1 / (1 + np.exp(-weighted_sum))
        return self.activation

    # multiply elementwise the derivative of the activation function by the upstream gradient and return
    def backward_propagation(self, upstream_gradient):
        # activation represents sig(z) and sig_prime(z) = sig(z)*(1-sig(z))
        sigmoid_prime = self.activation*(1-self.activation) 
        return np.multiply(sigmoid_prime, upstream_gradient)

    # place holder function to make SGD function readable, this layer has no parameters
    def update_parameters(self, mini_batch_size, eta):
        pass


# ==================================== Relu Layer ====================================
# the relu layer is a nonlinearity activation function layer

class ReluLayer:
    def __init__(self, layer_size):
        self.N = layer_size

        # column vector of activations
        self.activation = np.zeros((self.N,1))
    
    # apply the activation function on the weighted sum
    def forward_propagation(self, weighted_sum):
        self.activation = np.maximum(weighted_sum,0)
        return self.activation

    # multiply elementwise the derivative of the activation function by the upstream gradient and return
    def backward_propagation(self, upstream_gradient):
        relu_prime = (self.activation > 0)
        return np.multiply(relu_prime, upstream_gradient)

    # place holder function to make SGD function readable, this layer has no parameters
    def update_parameters(self, mini_batch_size, eta):
        pass


# ==================================== Softmax Layer ====================================
# the softmax layer is an output function layer

class SoftmaxLayer:
    def __init__(self, layer_size):
        self.N = layer_size

        # column vector of activations
        self.activation = np.zeros((self.N,1))
    
    # apply the softmax formula
    def forward_propagation(self, weighted_sum):
        self.activation = np.exp(weighted_sum) / (np.sum(np.exp(weighted_sum)))
        return self.activation

    # softmax will be used with cross entropy loss, the derivative will account for softmax derivative
    # and will skip the softmax layer on backprop anyways to simplify
    def backward_propagation(self, upstream_gradient):
        return upstream_gradient

    # place holder function to make SGD function readable, this layer has no parameters
    def update_parameters(self, mini_batch_size, eta):
        pass


# ====================================== Input Layer ====================================
# this is a dummy layer used for the input to keep modular structure

class InputLayer:
    def __init__(self, layer_size):
        self.N = layer_size

        # column vector of activations
        self.activation = np.zeros((self.N,1))

    def update_parameters(self, mini_batch_size, eta):
        pass



'''===========================================================================================
   ====================================== COST FUNCTIONS =====================================
   ==========================================================================================='''

# calculate quadratic cost for one training sample
def quadratic_cost(expected_output, activation):
    return 1/2 * np.sum(np.square(expected_output-activation))

# derivatve of quadratic cost function
def quadratic_cost_prime(expected_output, activation):
    return (activation - expected_output)

# multi class cross entropy cost
def cross_entropy_cost(expected_output, activation):
    return -np.sum(expected_output*np.log(activation))

# combine dc_da*da_dz to get this simplified form for back prop
def cross_entropy_cost_prime_SM(expected_output, activation):
    return (activation - expected_output)

# calculate cross entropy cost for one sample (used with sigmoid)
# binary cross entropy
# def cross_entropy_cost(expected_output, activation):
#     return np.sum(np.nan_to_num(-expected_output*np.log(activation)-(1-expected_output)*np.log(1-activation)))

#binary cross entropy
# derivatve of cross entropy (use with sigmoid)
# def cross_entropy_cost_prime(expected_output, activation):
#     return (expected_output-activation) #/(activation*(1-activation)) 
    # this denominator cancels with sig_prime but can cause nan issues so remove it and account for in sigmoid layer



'''===========================================================================================
   ====================================== DRIVER CLASS =======================================
   ==========================================================================================='''

# this class is used to build and train a neural network from the layer classes
class Network:
    # pass in the input size, cost function, and the derivative of the cost function
    # if using softmax with cross entropy loss then set arg to true so can account for backprop simplification
    def __init__(self, input_size, cost, cost_prime, is_SM_CE=False):
        self.cost = cost
        self.cost_prime = cost_prime
        self.cost_points = [] # calclate cost for each epoch so can plot
        self.cost_points_test = []
        self.is_SM_CE = is_SM_CE

        # make a list of layers
        self.layers = []

        # add the input layer
        IL = InputLayer(input_size)
        self.layers.append(IL)

        self.prev_layer_size = input_size
    
    # append a fully connected layer to the network
    def add_fc_layer(self, layer_size):
        self.layers.append(FullyConnectedLayer(layer_size, self.prev_layer_size))
        self.prev_layer_size = layer_size

    # append a sigmoid layer to the network
    def add_sigmoid_layer(self, layer_size):
        self.layers.append(SigmoidLayer(layer_size))
        self.prev_layer_size = layer_size

    # append a relu layer to the network
    def add_relu_layer(self, layer_size):
        self.layers.append(ReluLayer(layer_size))
        self.prev_layer_size = layer_size

    # append a softmax layer to the network
    def add_softmax_layer(self, layer_size):
        self.layers.append(SoftmaxLayer(layer_size))
        self.prev_layer_size = layer_size
    
    # do a forward pass through the layer of the network
    def forward_pass(self, input_data):
        # set the input layer activations to the input data
        self.layers[0].activation = input_data
        output = input_data

        # for each layer (not including the input) do forward propagation
        for layer in range(1, len(self.layers)):
            output = self.layers[layer].forward_propagation(output)
        # print(output)
        return output

    # do a backward pass through the layer of the network, return the cost
    def backward_pass(self, expected_output):
        if self.is_SM_CE == False:
            # get the first upstream gradient, the derivative of the cost function w/r/t the activation of the output
            upstream_gradient = self.cost_prime(expected_output, self.layers[-1].activation)

            # print("first upstream gradient", upstream_gradient)
            
            # we backward pass from the last layer to the first hidden layer
            for layer in range(1, len(self.layers)):
                upstream_gradient = self.layers[-layer].backward_propagation(upstream_gradient)
        
        # back prop slighlty different for last layer when doing soft max with cross entropy loss
        else:
            upstream_gradient = upstream_gradient = self.cost_prime(expected_output, self.layers[-1].activation)
            # cost_prime combines softmax and cross entropy derivatives so skip softmax for backprop
            for layer in range(2, len(self.layers)):
                upstream_gradient = self.layers[-layer].backward_propagation(upstream_gradient)

        
    # update the parameters over the gradient of one mini batch (based on Nielson's code)
    def mini_batch_pass(self, eta, mini_batch):
        # forward and backward pass for all input samples, dw & db are calculated internally
        for input, output in mini_batch:
            self.forward_pass(input)
            self.backward_pass(output)

        # update the parameters
        for layer in range(1, len(self.layers)):
            self.layers[layer].update_parameters(len(mini_batch), eta)
    
    # the main driver function for the neural network (taken from Nielson's code)
    def stochastic_gradient_descent(self, training_data, epochs, mini_batch_size, eta, test_data=None): 
        # if test data is provided, then the network will be evaluated during training
        if test_data: 
            n_test = len(test_data)
        
        n = len(training_data)

        # main training loop
        for j in range(epochs):
            random.shuffle(training_data) # shuffle the training data
            
            # create a list of mini batches by splitting the training data in intervals of mini_batch_size
            # n is the number of items in the training data
            # here range means to iterate from 0 to n by interval of mini_batch_size
            # so mini_bathes[0] = training_data[0:mini_batch_size]
            mini_batches = [
                training_data[k:k+mini_batch_size] for k in range(0, n, mini_batch_size)
                ]
           
            # once the mini batches are created update the network w's and b's by 
            # doing gradient descent for each mini batch
            for mini_batch in mini_batches:
                self.mini_batch_pass(eta, mini_batch)

            # after updating the parameters check the cost
            cost_amount = 0
            for input, output in training_data:
                activation = self.forward_pass(input)
                cost_amount += self.cost(output, activation)
            self.cost_points.append(cost_amount/len(training_data))
                
            # if have test data, then evaluate the network at each epoch    
            if test_data:
                # get the cost for the test data to compare to the training data
                cost_amount_test = 0
                for input, output in test_data:
                    activation = self.forward_pass(input)
                    cost_amount_test += self.cost(output, activation)
                self.cost_points_test.append(cost_amount_test/len(test_data))
                #print("Epoch {0}: Train_data: {1} / {2}".format(j, self.test_network(training_data), len(training_data)))
                print("Epoch {0}: Test_data: {1} / {2}".format(j, self.test_network(test_data), n_test), "Train Cost = ", cost_amount/len(training_data), "Test Cost = ", cost_amount_test/len(test_data))
            else:
                print("Epoch {0} complete".format(j))
        
        plt.plot(self.cost_points, label="train")
        plt.plot(self.cost_points_test, label="test")
        plt.legend()
        plt.show()


    # function to calculate how many test data samples are classified correctly
    def test_network(self, test_data):
        # test_results looks like [index, output col vector]
        test_results = [(np.argmax(self.forward_pass(input)), output) for (input, output) in test_data]

        return sum(int(output[max_index] == 1) for (max_index, output) in test_results)