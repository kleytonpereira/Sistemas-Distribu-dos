import java.io.*;
import java.net.*;
import java.util.*;

/*
 * Servidor para processar as requisicoes de Ping sobre UDP.
 *
 * Uso:  java PingServer <porta>
 *
 * Fica em loop infinito escutando pacotes UDP. Quando um pacote chega, devolve
 * (eco) os mesmos dados para o cliente, simulando perda de pacotes (LOSS_RATE)
 * e atraso de rede (AVERAGE_DELAY).
 *
 * Compativel com o cliente em Python (ping_client.py): o formato da mensagem e
 * "PING <seq> <time>\r\n" e o servidor nao interpreta o conteudo -- so ecoa.
 */
public class PingServer {

    private static final double LOSS_RATE = 0.3;      // 30% dos pacotes sao descartados
    private static final int AVERAGE_DELAY = 100;     // atraso medio simulado, em ms
    private static DatagramSocket socket;

    public static void main(String[] args) throws Exception {

        // Obter o argumento da linha de comando.
        if (args.length != 1) {
            System.out.println("Required arguments: port");
            return;
        }
        int port = Integer.parseInt(args[0]);

        // Gerador de numeros aleatorios p/ simular perda de pacotes e atrasos na rede.
        Random random = new Random();

        // O socket e criado UMA vez, fora do laco. (Cria-lo dentro do while
        // provocaria BindException na segunda volta, pois a porta ja estaria em uso.)
        socket = new DatagramSocket(port);

        System.out.println("PingServer escutando na porta " + port
                + " (LOSS_RATE=" + LOSS_RATE + ", AVERAGE_DELAY=" + AVERAGE_DELAY + "ms)");

        while (true) {
            byte[] buffer = new byte[1024];

            // Criar um pacote de datagrama para comportar o pacote UDP de chegada.
            DatagramPacket request = new DatagramPacket(buffer, buffer.length);

            // Bloquear ate que o hospedeiro receba o pacote UDP.
            socket.receive(request);

            // Imprimir os dados recebidos.
            printData(request);

            // Decidir se responde, ou simula perda de pacotes.
            if (random.nextDouble() < LOSS_RATE) {
                System.out.println("Reply not sent.");
                continue;
            }

            // Simular o atraso da rede: de 0 a 2x o atraso medio.
            // (Cuidado com a versao do PDF: o cast estava no lugar errado --
            //  (int)(random.nextDouble()) e sempre 0, entao nunca havia atraso.)
            Thread.sleep((long) (random.nextDouble() * 2 * AVERAGE_DELAY));

            // Enviar resposta.
            InetAddress clientHost = request.getAddress();
            int clientPort = request.getPort();
            byte[] buf = request.getData();

            // Usar request.getLength() -- assim o eco devolve apenas os bytes que
            // chegaram, e nao os 1024 bytes do buffer com lixo/zeros no final.
            DatagramPacket reply = new DatagramPacket(buf, request.getLength(),
                                                      clientHost, clientPort);
            socket.send(reply);

            System.out.println("Reply sent.");
        }
    }

    /*
     * Imprimir o dado de Ping no trecho de saida padrao.
     */
    private static void printData(DatagramPacket request) throws Exception {
        // Obter referencia para a ordem de pacotes de bytes.
        byte[] buf = request.getData();

        // Envolver os bytes numa cadeia de entrada vetor de bytes, de modo que
        // voce possa ler os dados como uma cadeia de bytes.
        ByteArrayInputStream bais = new ByteArrayInputStream(buf, 0, request.getLength());

        // Envolver a cadeia num leitor de cadeia de entrada, de modo que voce
        // possa ler os dados como uma cadeia de caracteres.
        InputStreamReader isr = new InputStreamReader(bais);

        // Envolver o leitor num leitor com armazenagem, de modo que voce possa
        // ler os dados de caracteres linha a linha. (A linha e uma sequencia de
        // caracteres terminados por alguma combinacao de \r e \n.)
        BufferedReader br = new BufferedReader(isr);

        // O dado da mensagem esta contido numa unica linha, entao leia esta linha.
        String line = br.readLine();

        // Imprimir o endereco do hospedeiro e o dado recebido dele.
        System.out.println("Received from "
                + request.getAddress().getHostAddress() + ":"
                + request.getPort() + " -> " + line);
    }
}