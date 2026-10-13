import torch
import torch.nn as nn
import torch.optim as optim


def sigmoid(x):
    return 1 / (1 + torch.exp(-x))

class Lstm(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.h = hidden_size
        self.i = input_size
        self.forget_nn = nn.Parameter(torch.randn(self.i + self.h, self.h))
        self.remember_nn = nn.Parameter(torch.randn(self.i + self.h, self.h))
        self.forget_bias_nn = nn.Parameter(torch.randn(self.h))

        self.remember_bias_nn = nn.Parameter(torch.randn(self.h))
        self.candidate_nn = nn.Parameter(torch.randn(self.i + self.h, self.h))
        self.candidate_bias_nn = nn.Parameter(torch.randn(self.h))
        self.output_nn = nn.Parameter(torch.randn(self.i + self.h, self.h))
        self.output_bias_nn = nn.Parameter(torch.randn(self.h))
        self.theta = sigmoid
        self.linear = nn.Linear(self.h, self.i)

    def forward_single_time(self, input_single_time):
        concat_input = torch.concat([self.hidden, input_single_time], axis=1)
        input_after_forget = self.theta(concat_input @ self.forget_nn + self.forget_bias_nn)
        input_after_remember = self.theta(concat_input @ self.remember_nn + self.remember_bias_nn)
        candidate = torch.tanh(concat_input @ self.candidate_nn + self.candidate_bias_nn)
        ct = input_after_forget * self.core + input_after_remember * candidate
        self.core = ct
        output = self.theta(concat_input @ self.output_nn + self.output_bias_nn)
        self.hidden = output * torch.tanh(self.core)
        return self.hidden

    def forward(self, input_seq, core=None, hidden=None):
        batch_size = input_seq.shape[0]
        if core is None and hidden is None:
            self.core = torch.zeros(batch_size, self.h)
            self.hidden = torch.zeros(batch_size, self.h)
        else:
            self.core = core
            self.hidden = hidden
        seq_size = input_seq.shape[1]
        hidden_seq = torch.zeros(batch_size, seq_size, self.h)
        for i in range(seq_size):
            input_single = input_seq[:,i,:]
            hidden_seq[:,i,:] = self.forward_single_time(input_single)
        return self.linear(hidden_seq), (self.hidden, self.core)


if __name__ == "__main__":
    batch_size = 50
    input_size = 5
    hidden_size = 10
    time_seq = 3
    lstm = Lstm(input_size, hidden_size)
    optimm = optim.SGD(lstm.parameters(), lr=0.01)
    # print(list(lstm.named_parameters()))
    lstm2 = Lstm(input_size, hidden_size)
    # output_seq = np.zeros((batch_size, time_seq, hidden_size))
    input = torch.randn(batch_size, time_seq, input_size)
    input_2 = torch.randn(batch_size, 2*time_seq, input_size)
    input_2_slice_1 = input_2[:,:time_seq,:]
    input_2_slice_2 = input_2[:,time_seq:,:]
    input_2_slices = torch.zeros(2*time_seq - time_seq + 1, batch_size, time_seq, input_size)
    for i in range(time_seq, 2*time_seq + 1):
        input_2_slices[i - time_seq] = input_2[:,i - time_seq:i,:]
    # for i in range(time_seq):
    #     output = lstm(input[:,i,:])
    #     assert output.shape[0] == batch_size
    #     assert output.shape[1] == hidden_size
    #     output_seq[:,i,:] = output
    epoch = 100
    for i in range(epoch):
        slices_len = len(input_2_slices)
        index = i % slices_len
        data = input_2_slices[index]
        data_1 = input_2_slices[index + 1] if index < slices_len - 1 else input_2_slices[0]
        optimm.zero_grad()
        output_seq, (hidden, core) = lstm(data)
        # output_seq_2, (hidden2, core2) = lstm2(input_2_slice_1)
        # output_seq_2_2, (hidden2, core2) = lstm2(input_2_slice_2, core2, hidden2)
        # output_seq_3 = np.concat([output_seq_2, output_seq_2_2], axis=1)
        # print(output_seq.shape)
        # output_seq.retain_grad()
        loss = torch.sum(torch.abs(output_seq - data_1))
        index_newest = index + time_seq
        if index_newest >= slices_len:
            input_2_slices = torch.concat([input_2_slices, torch.stack([output_seq])], axis=0)
        print(loss)
        loss.backward()
        # print(output_seq.grad.shape)
        # for name, param in list(lstm.named_parameters()):
        #     print(param.grad.shape)
        optimm.step()
    # print(list(lstm.named_parameters()))
    # print(output_seq_3.shape)
    # print(hidden2.shape)
    # print(core.shape)
    # print(np.allclose(output_seq, output_seq_3))
