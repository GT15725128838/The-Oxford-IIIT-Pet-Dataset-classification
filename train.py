import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader
from net import Net


def load_images_and_labels(dataset_dir):
    images = []
    labels = []
    # 遍历图片
    for file_name in sorted(os.listdir(dataset_dir)):
        if file_name.endswith('.jpg'):
            image_path = os.path.join(dataset_dir, file_name)
            # 读取图片
            image = cv2.imread(image_path)
            # 转换成RGB模式
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # 统一图片尺寸
            image = cv2.resize(image, (224, 224))
            # 归一化
            image = image / 255.0
            images.append(image)
            labels.append(file_name.split('_')[0])
    return np.array(images), np.array(labels)


# 创建自定义数据集类
class PetDataset(Dataset):
    def __init__(self, images, labels):
        self.images = images
        self.labels = labels

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image = self.images[index]
        label = self.labels[index]
        return torch.Tensor(image), label


if __name__ == '__main__':
    # 图片路径
    dataset_dir = './data/images/'
    images, labels = load_images_and_labels(dataset_dir)
    # 标签编码
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(images, labels_encoded, test_size=0.2, random_state=42)

    # 调用类加载图像和标签
    train_dataset = PetDataset(X_train, y_train)
    test_dataset = PetDataset(X_test, y_test)

    # 调用网络模型
    model = Net()

    # 设置损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 加载训练数据
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    # 迭代次数
    num_epochs = 10
    # 判断是否存在cuda
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    # 迭代训练
    for epoch in range(num_epochs):
        running_loss = 0.0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
        # 输出训练过程损失函数
        print('Epoch [{}/{}], Loss: {:.4f}'.format(epoch + 1, num_epochs, running_loss / len(train_loader)))

        # 测试集预测准确率
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        accuracy = 100 * correct / total
        print('Test Accuracy: {:.2f}%'.format(accuracy))