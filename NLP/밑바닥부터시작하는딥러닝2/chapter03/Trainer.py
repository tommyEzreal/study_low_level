# trainer

import sys
sys.path.append('..')
import numpy
import time
import matplotlib.pyplot as plt
from common.np import *
from common.util import clip_grads
from common.optimizer import Adam
from common.util import preprocess


class Trainer:
    def __init__(self, model, optimizer):
        self.model = model
        self.optimizer = optimizer
        self.loss_list = []
        self.eval_interval = None
        self.current_epoch = 0

    def fit(self, x, t, max_epoch = 10, batch_size =32, max_grad=None, eval_interval = 20):
        data_size = len(x)
        max_iters = data_size // batch_size
        self.eval_interval = eval_interval #do evaluation interval 

        model, optimizer = self.model, self.optimizer
        
        total_loss = 0
        loss_count = 0

        start_time = time.time()
        for epoch in range(max_epoch):
            # shuffle data idx 
            idx = numpy.random.permutation(numpy.arange(data_size))
            x = x[idx]
            t = t[idx]

            for iters in range(max_iters): # iteration
                batch_x = x[iters*batch_size : (iters+1)*batch_size] #slice by batch size 
                batch_t = t[iters*batch_size : (iters+1)*batch_size]

                loss = model.forward(batch_x, batch_t) # to forward pass of model
                model.backward() #backward grad 
                params, grads = remove_duplicate(model.params, model.grads)
                if max_grad is not None:
                    clip_grads(grads, max_grad)
                optimizer.update(params, grads)
                total_loss += loss
                loss_count +=1

                if (eval_interval is not None) and (iters % eval_interval) ==0:
                    avg_loss = total_loss / loss_count
                    elapsed_time = time.time() - start_time
                    print('epoch %d | iteration %d/%d | time %d[s] | loss %.2f'
                    % (self.current_epoch+1, iters+1, max_iters, elapsed_time, avg_loss ))
                    self.loss_list.append(float(avg_loss))
                    total_loss, loss_count = 0,0
            
            self.current_epoch += 1


    def plot(self, ylim=None):
        x = numpy.arange(len(self.loss_list))
        if ylim is not None:
            plt.ylim(*ylim)
        plt.plot(x, self.loss_list, label='train')
        plt.xlabel('iteration (x' + str(self.eval_interval) + ')')
        plt.ylabel('loss')
        plt.show()

def remove_duplicate(params, grads):
    '''
    매개변수 배열 중 중복되는 가중치를 하나로 모아
    그 가중치에 대응하는 기울기를 더한다.
    '''
    params, grads = params[:], grads[:]  # copy list

    while True:
        find_flg = False
        L = len(params)

        for i in range(0, L - 1):
            for j in range(i + 1, L):
                # 가중치 공유 시
                if params[i] is params[j]:
                    grads[i] += grads[j]  # 경사를 더함
                    find_flg = True
                    params.pop(j)
                    grads.pop(j)
                # 가중치를 전치행렬로 공유하는 경우(weight tying)
                elif params[i].ndim == 2 and params[j].ndim == 2 and \
                     params[i].T.shape == params[j].shape and np.all(params[i].T == params[j]):
                    grads[i] += grads[j].T
                    find_flg = True
                    params.pop(j)
                    grads.pop(j)

                if find_flg: break
            if find_flg: break

        if not find_flg: break

    return params, grads     


if __name__ == '__main__':
    window_size = 1
    hidden_size = 5
    batch_size = 3
    max_epoch = 1000

    text = 'You say goodbye and I say hello.'
    # make corpus, word_id index 
    corpus, word_to_id, id_to_word = preprocess(text)

    vocab_size = len(word_to_id)
    # make contexts, target vectors(array) 
    contexts, target = create_contexts_target(corpus, window_size)
    # make arrays into onehot representation
    target = convert_one_hot(target, vocab_size)
    contexts = convert_one_hot(contexts, vocab_size)

    #load model & trainer
    model = CBOW(vocab_size, hidden_size)
    optimizer = Adam() # common.optimizer 
    trainer = Trainer(model,optimizer)

    #train
    trainer.fit(contexts, target, max_epoch, batch_size)
    trainer.plot()

    # dense representation of words 
    word_vecs = model.word_vecs
    for word_id, word in id_to_word.items():
        print(word, word_vecs[word_id])
