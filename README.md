Trabalho testado no Core.
Depois de abrir o servidor numa máquina com o código do Server, outras máquinas que corram o código Node, seram ligados ao servidor através de uma ligação TCP, os Nodes podem requisitar um ficheiro ao Server, que envia ao Node os IP's dos Nodes que possuem esse ficheiro. 
Depois de receber essa informação o Node dá ping a todos os Nodes dessa lista e vê qual envia a resposta mais rápida, em seguida o Node envia uma mensagem UDP a requisitar o ficheiro e o Node que recebe esse pedido deve devolver o ficheiro.
No final de todo este processo o Server atualiza a sua base de dados.
