# %% [markdown]
# # Code describe the line of reasoning we need to show for all the cases

# %%
#https://anbasile.github.io/posts/2017-06-25-jupyter-venv/

# %%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model, model_selection
from sklearn.metrics import mean_squared_error, r2_score

# %% [markdown]
# # Load data

# %%
B = pd.read_parquet('./data/B_HKML.parquet')

# %%
B = B[B['date'] < '2022-05-01']

# %%
X_df = pd.read_parquet('./data/XB_PCA_HKML.parquet')

# %%
X_df = X_df[X_df['date'] < '2022-05-01']

# %%
y_df = pd.read_parquet('./data/Y_HKML.parquet')

# %%
y_df = y_df.iloc[X_df.index]

# %%
X_df.shape, y_df.shape, B.shape

# %% [markdown]
# # Train-test split

# %%
moons = X_df.date.unique()

# %%
moon_train = moons[:230] 
moon_test = moons[260:]

# %% [markdown]
# # Define loss function

# %%
error_lis = []

# %%
def custom_loss2(y_pred, y_true, b_moon):
    Omega = torch.eye(len(y_true)) - torch.mm(b_moon, torch.pinverse(b_moon))
    z_hat = torch.mm(Omega, y_pred)
    
    #error = torch.sum((z_hat - y_true)**2) / len(y_true)
    #error = torch.mm((z_hat - y_true).T, z_hat - y_true)/len(y_true)
    error = torch.linalg.norm(z_hat - y_true)/len(y_true)
    #error_lis.append(error)
    
    return error

# %% [markdown]
# # Train model and predict

# %%
import torch
import numpy as np
import pandas as pd
import torch.nn as nn
from tqdm import tqdm

# %%
# As this notebook shows a simple linear model, there is no need to introduce validation data, i.e. 
# the training is deterministic and only one epoch is necessary to perform it.
# Nevertheless, this section should train such that the validation loss is minimized.

# %%
class RegressionModel(torch.nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(RegressionModel, self).__init__()
        self.fc1 = torch.nn.Linear(input_size, hidden_size)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(hidden_size, hidden_size)
        self.fc3 = torch.nn.Linear(hidden_size, output_size)
        #self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        hidden = self.fc1(x)
        relu_output = self.relu(hidden)
        #dropout = self.dropout(relu_output)
        hidden2 = self.fc2(relu_output)
        relu_output = self.relu(hidden2)
        #dropout = self.dropout(relu_output)
        y_pred = self.fc3(relu_output)
        return y_pred

# %%
# Create an instance of the model
model = RegressionModel(input_size=160, hidden_size=512, output_size=1) # hidden size ==> 500 ==> loss: inf ==> exploding gradient

loss_mse = nn.MSELoss()
# Define the optimizer
optimizer = torch.optim.Adam(model.parameters())

# train model for 5 epochs using custom loss function
num_epochs = 20

# %%
for i in tqdm(range(num_epochs)):
    print(f"Epoch {i+1}")
    # create minibatch of data
    #batch_size = 100
    for moon in moons[:230]:
        #pdb.set_trace()
        X_moon = torch.from_numpy(X_df[X_df.date == moon].drop(columns=["date"]).values).to(torch.float32)
        y_moon = torch.from_numpy(y_df[X_df.date == moon].values.reshape(-1,1)).to(torch.float32)
        import pdb
        pdb.set_trace()
        b_moon = torch.from_numpy(B[B.date == moon].drop(columns=["date"]).values).to(torch.float32)
        #import pdb
        #pdb.set_trace()
        y_pred = model(X_moon)
        #loss = custom_loss2(y_pred, y_moon, b_moon)
        loss = loss_mse(y_pred, y_moon)
        error_lis.append(loss.item())
        
        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
    # Print the loss every 100 epochs
    if (i + 1) % 5 == 0:
        print('Epoch [{}/{}], Loss: {:.4f}'.format(i+1, num_epochs, loss.item()))

# %%
plt.plot(error_lis)

# %%
plt.plot(error_lis)

# %%
y_hat =  model(torch.from_numpy(X_df[X_df.date > moons[260]].drop(columns=["date"]).values).to(torch.float32)).detach().numpy()

# %%
y_test = y_df[X_df.date > moons[260]].values.reshape(-1,1)

# %%
y_hat.shape, y_test.shape

# %%


# %% [markdown]
# # Scatter plot to show linear relation between Y and y_hat

# %%
from scipy.stats import linregress

# %%
slope, intercept, r_value, p_value, std_err = linregress(y_test, y_hat)
plt.scatter(y_test, y_hat)
plt.plot(y_test, slope * y_test + intercept,'r')
plt.show()

# %%
y_hat_df = pd.DataFrame()
y_hat_df['date'] = X_df[X_df['date'] > moons[260]].date
y_hat_df['y_hat'] = y_hat
y_hat_df['Y'] = y_test

# %%
y_hat_df # custom_fitenss

# %%
y_hat_df # mse_fitness

# %% [markdown]
# # Spearman

# %%
def spear(x):
    return x.corr(method='spearman').iloc[0, 1]

# %%
spearman = y_hat_df.groupby("date").apply(lambda x: spear(x))

# %%
spearman.mean(), spearman.shape # 46 values for 46 moons

# %%
spearman.plot()
plt.axhline(y=spearman.mean(), color='r', linestyle='-')
plt.show()

# %%
spearman.hist(bins=30)
plt.axvline(x=spearman.mean(), color='r', linestyle='-')

# %% [markdown]
# # MSE

# %%
mse = y_hat_df.groupby('date').apply(lambda x: mean_squared_error(x.y_hat, x.Y))

# %%
mse.plot()
plt.axhline(y=mse.mean(), color='r', linestyle='-')
plt.show()

# %%
mse.hist(bins=30)
plt.axvline(x=mse.mean(), color='r', linestyle='-')

# %% [markdown]
# # Orthogonalize output and show same results.

# %%
B = B[X_df.date > moons[260]]

# %%
B

# %%
y_hat_date = y_hat_df[['date', 'y_hat']] 



# %%
import sys
sys.path.insert(1, "/Users/utkarshpratiush/Cr_D/Feature engg/feature-engineering/src")
from class_ import Data

# %%
data = Data(f_matrix=y_hat_date, b_matrix=B)

# %%
data.orthogonalize()

# %%
data.f_matrix

# %%
y_hat_df.y_hat = data.f_matrix.y_hat

# %%
y_hat_df

# %%
slope, intercept, r_value, p_value, std_err = linregress(y_hat_df.Y,y_hat_df.y_hat)
plt.scatter(y_hat_df.Y, y_hat_df.y_hat)
plt.plot(y_hat_df.Y, slope * y_hat_df.Y + intercept,'r')
plt.show()

# %%
spearman = y_hat_df.groupby("date").apply(lambda x: spear(x))
spearman.plot()
plt.axhline(y=spearman.mean(), color='r', linestyle='-')
plt.show()

# %%
spearman.hist(bins=30)
plt.axvline(x=spearman.mean(), color='r', linestyle='-')

# %%
mse = y_hat_df.groupby('date').apply(lambda x: mean_squared_error(x.y_hat, x.Y))
mse.plot()
plt.axhline(y=mse.mean(), color='r', linestyle='-')
plt.show()

# %%
mse.hist(bins=30)
plt.axvline(x=mse.mean(), color='r', linestyle='-')

# %%


